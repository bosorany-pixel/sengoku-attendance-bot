"""
Attendance pinger: fetches /stats/mordor from the API and pings Discord members
whose Albion attendance is less than half of the guild max.
Runs once (e.g. via cron). Sends pings in a configured channel.

Run: API_URL=http://localhost:8123 DISCORD_TOKEN=... python -m src.attendance_pinger
"""
import os
import sys
from datetime import datetime, date, timedelta

_srcdir = os.path.dirname(os.path.abspath(__file__))
if _srcdir not in sys.path:
    sys.path.insert(0, os.path.dirname(_srcdir))

import discord
import requests

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

GUILD_ID = 1436061961136640075
CHANNEL_ID = 1448731680805359748
API_URL = os.environ.get("API_URL", "http://localhost:8100").rstrip("/")


def fetch_mordor_stats() -> dict | None:
    """GET /stats/mordor and return JSON or None on failure."""
    try:
        r = requests.get(f"{API_URL}/stats/mordor", timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Failed to fetch stats: {e}", file=sys.stderr)
        return None


def low_attendance_players(data: dict) -> list[dict]:
    """Return list of players with attendance < half of guild max."""
    players = data.get("players") or []
    if not players:
        return []
    max_att = max(p.get("attendance", 0) for p in players)
    if max_att <= 0:
        return []
    threshold = max_att / 3.0
    return [p for p in players if p.get("attendance", 0) < threshold]


def _name_match(discord_name: str | None, albion_name: str) -> bool:
    if not discord_name or not albion_name:
        return False
    return discord_name.strip().lower() == albion_name.strip().lower()


def match_members_to_players(
    members: list[discord.Member],
    player_names: list[str],
) -> list[discord.Member]:
    """Return Discord members that match any of the given Albion player names."""
    matched: list[discord.Member] = []
    seen_ids: set[int] = set()
    for name in player_names:
        for m in members:
            if m.id in seen_ids:
                continue
            if _name_match(m.display_name, name) or _name_match(getattr(m, "global_name", None) or m.name, name):
                matched.append(m)
                seen_ids.add(m.id)
                break
    return matched


async def run_pinger(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild {GUILD_ID} not found. Bot is in: {[g.name for g in client.guilds]}", file=sys.stderr)
        return
    channel = guild.get_channel(CHANNEL_ID) or await guild.fetch_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel {CHANNEL_ID} not found", file=sys.stderr)
        return

    data = fetch_mordor_stats()
    if not data:
        return
    low = low_attendance_players(data)
    if not low:
        await channel.send("Посещаемость: все на уровне или выше половины от макс. — пинг не нужен.")
        return

    player_names = [p.get("name", "").strip() for p in low if p.get("name")]
    if not player_names:
        await channel.send("Низкая посещаемость: не удалось определить имена игроков.")
        return

    members: list[discord.Member] = []
    async for m in guild.fetch_members(limit=None):
        members.append(m)

    to_ping = match_members_to_players(members, player_names)
    max_att = max(p.get("attendance", 0) for p in data.get("players") or [])
    threshold = max_att / 3.0

    header = (
        f"**Низкая посещаемость** (меньше половины от макс. {max_att} за неделю): "
        f"порог {threshold:.0f}. \nАЛО ПАРНИ НА КОНТЕНТ ХОДИТЬ БУДЕМ???\n"
    )
    if not to_ping:
        await channel.send(
            header + "никто из списка не найден на сервере Discord. "
            f"Имена из Albion BB: {', '.join(player_names[:20])}{'…' if len(player_names) > 20 else ''}."
        )
        return

    mentions = " ".join(m.mention for m in to_ping)
    msg = header + mentions
    if len(msg) > 2000:
        await channel.send(header)
        chunk = 1800
        for i in range(0, len(mentions), chunk):
            msg = await channel.send(mentions[i : i + chunk])
    else:
        msg = await channel.send(msg)
    thread = await msg.create_thread(name="ваши оправдания")
    await thread.send("https://europe.albionbb.com/guilds/nJTbhlRxTh2RAGMclSKk7A/attendance?minPlayers=20&start=" + (date.today() - timedelta(days=7)).strftime("%Y-%m-%d"))


def main():
    token = os.environ.get("DISCORD_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("Set DISCORD_TOKEN or DISCORD_BOT_TOKEN", file=sys.stderr)
        sys.exit(1)

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        await run_pinger(client)
        await client.close()

    client.run(token)


if __name__ == "__main__":
    main()
