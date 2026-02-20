"""
POV collector: runs once (e.g. daily via cron).
Reads a Discord forum channel where each thread is a user topic.
Counts per user (thread owner):
  - pov_count: messages with any link posted by the user in their topic
  - checked_pov_count: those link messages that have at least one Discord reaction
Stores results in USERS.pov_count and USERS.checked_pov_count.

Run: DISCORD_TOKEN=... python -m src.pov_collector
Cron (daily at 03:00): 0 3 * * * cd /path/to/repo && DISCORD_TOKEN=... python -m src.pov_collector
"""
import os
import re
import sys

# Allow running as python -m src.pov_collector from repo root
_srcdir = os.path.dirname(os.path.abspath(__file__))
if _srcdir not in sys.path:
    sys.path.insert(0, _srcdir)

import discord
import dotenv
import db_worker as dbw

dotenv.load_dotenv()

GUILD_ID = 1436061961136640075
FORUM_CHANNEL_ID = 1450036220771045427

TOKEN = os.getenv("DISCORD_TOKEN") 

# Any URL-like pattern (http, https, discord.gg, etc.)
URL_PATTERN = re.compile(
    r"https?://[^\s<>]+|discord\.gg/[^\s<>]+|discordapp\.com/[^\s<>]+",
    re.IGNORECASE,
)


def message_has_link(message: discord.Message) -> bool:
    """True if message content or embeds contain any link."""
    if message.content and URL_PATTERN.search(message.content):
        return True
    for embed in message.embeds:
        if embed.url and URL_PATTERN.search(embed.url):
            return True
        if embed.description and URL_PATTERN.search(embed.description):
            return True
    return False


def message_has_reaction(message: discord.Message) -> bool:
    """True if message has at least one reaction."""
    return len(message.reactions) > 0


async def collect_thread(
    thread: discord.Thread,
    owner_id: int,
) -> tuple[int, int, str | None, str | None]:
    """
    Count in this thread (user topic): messages by owner with a link (pov_count),
    and of those how many have any reaction (checked_pov_count).
    Also return ISO timestamps of the most recent such message: last_pov, last_checked_pov.
    Returns (pov_count, checked_pov_count, last_pov_iso, last_checked_pov_iso).
    """
    pov = 0
    checked = 0
    last_pov_ts = None
    last_checked_ts = None
    try:
        async for msg in thread.history(limit=None):
            if msg.author.id != owner_id:
                continue
            if not message_has_link(msg):
                continue
            pov += 1
            if last_pov_ts is None or msg.created_at > last_pov_ts:
                last_pov_ts = msg.created_at
            if message_has_reaction(msg):
                checked += 1
                if last_checked_ts is None or msg.created_at > last_checked_ts:
                    last_checked_ts = msg.created_at
    except (discord.Forbidden, discord.HTTPException) as e:
        print(f"  [pov_collector] thread {thread.id} ({thread.name}): {e}", file=sys.stderr)
    last_pov_iso = last_pov_ts.isoformat() if last_pov_ts else None
    last_checked_iso = last_checked_ts.isoformat() if last_checked_ts else None
    return (pov, checked, last_pov_iso, last_checked_iso)


def main():
    if not TOKEN:
        print("Set DISCORD_TOKEN or DISCORD_BOT_TOKEN", file=sys.stderr)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.guilds = True
    intents.message_content = True
    client = discord.Client(intents=intents)
    db = dbw.DBWorker()

    def _channel_type_name(ch):
        """Human-readable channel type (class name + numeric type if available)."""
        name = type(ch).__name__
        if hasattr(ch, "type"):
            try:
                name += f" (type={ch.type})"
            except Exception:
                pass
        return name

    async def run():
        # Use only cached guilds: bot must be a member. fetch_guild() 404s if bot is not in the guild.
        guild = client.get_guild(GUILD_ID)
        if guild is None:
            names = [f"{g.name!r} ({g.id})" for g in client.guilds]
            print(f"Guild {GUILD_ID} not found. Bot is in: {names or 'no guilds'}. Is the bot invited to the server? Is GUILD_ID correct?", file=sys.stderr)
            return

        # Map server: list all channels so we can see what the target is
        print("--- Guild channel map ---")
        for ch in sorted(guild.channels, key=lambda c: (getattr(c, "position", 0), c.id)):
            parent = getattr(ch, "category", None)
            parent_info = f" (in category: {parent.name})" if parent else ""
            marker = " <-- TARGET" if ch.id == FORUM_CHANNEL_ID else ""
            print(f"  id={ch.id} name={ch.name!r} {_channel_type_name(ch)}{parent_info}{marker}")
        print("-------------------------")

        channel = guild.get_channel(FORUM_CHANNEL_ID) or await guild.fetch_channel(FORUM_CHANNEL_ID)
        if channel is None:
            print(f"Channel {FORUM_CHANNEL_ID} not found", file=sys.stderr)
            return

        # If target is a category, collect from all forum channels under it
        channels_to_scan: list = []
        if isinstance(channel, discord.CategoryChannel):
            for ch in channel.channels:
                if isinstance(ch, discord.ForumChannel) or (
                    getattr(ch, "threads", None) is not None and hasattr(ch, "archived_threads")
                ):
                    channels_to_scan.append(ch)
            if not channels_to_scan:
                print(f"Category {channel.name!r} has no forum/thread channels", file=sys.stderr)
                return
            print(f"Scanning {len(channels_to_scan)} forum(s) under category {channel.name!r}")
        else:
            has_threads = getattr(channel, "threads", None) is not None and hasattr(channel, "archived_threads")
            if not has_threads:
                print(f"Channel {FORUM_CHANNEL_ID} is {_channel_type_name(channel)} (no .threads/.archived_threads)", file=sys.stderr)
                return
            channels_to_scan = [channel]
            print(f"Using channel {channel.name!r} ({_channel_type_name(channel)})")

        all_threads: list[discord.Thread] = []
        for ch in channels_to_scan:
            all_threads.extend(ch.threads)
            try:
                async for thread in ch.archived_threads(limit=100):
                    all_threads.append(thread)
            except (discord.HTTPException, discord.Forbidden) as e:
                print(f"  {ch.name!r} archived_threads: {e}", file=sys.stderr)
        print(f"Total threads: {len(all_threads)}")

        # Aggregate per user (uid -> (pov_sum, checked_sum, best_last_pov_iso, best_last_checked_iso))
        by_uid: dict[int, tuple[int, int, str | None, str | None]] = {}
        for thread in all_threads:
            owner_id = thread.owner_id if hasattr(thread, "owner_id") else getattr(thread, "owner_id", None)
            if owner_id is None:
                continue
            pov, checked, last_pov_iso, last_checked_iso = await collect_thread(thread, owner_id)
            db.ensure_user_for_pov(owner_id, thread.name)
            if owner_id not in by_uid:
                by_uid[owner_id] = (0, 0, None, None)
            prev_pov, prev_checked, prev_last, prev_last_checked = by_uid[owner_id]
            new_last = max(filter(None, [prev_last, last_pov_iso])) if (prev_last or last_pov_iso) else None
            new_last_checked = max(filter(None, [prev_last_checked, last_checked_iso])) if (prev_last_checked or last_checked_iso) else None
            by_uid[owner_id] = (
                prev_pov + pov,
                prev_checked + checked,
                new_last,
                new_last_checked,
            )
            print(f"  {thread.name} (uid={owner_id}): pov={pov} checked={checked}")

        for uid, (pov_sum, checked_sum, last_pov_iso, last_checked_iso) in by_uid.items():
            db.update_pov_counts(uid, pov_sum, checked_sum, last_pov_iso, last_checked_iso)
            print(f"  -> uid={uid}: total pov={pov_sum} checked={checked_sum} last_pov={last_pov_iso or '-'} last_checked={last_checked_iso or '-'}")

    @client.event
    async def on_ready():
        print(f"POV collector: logged in as {client.user}, guild={GUILD_ID} forum={FORUM_CHANNEL_ID}")
        await run()
        await client.close()

    client.run(TOKEN)


if __name__ == "__main__":
    main()
