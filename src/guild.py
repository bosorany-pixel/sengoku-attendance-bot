import asyncio
import os
import discord
from discord.ext import commands
import dotenv
import src.db_worker as dbw
import src.datatypes as datatypes
import src.common as common
dotenv.load_dotenv()

db_worker = dbw.DBWorker()


async def get_nicks(guild_id: int, local_bot: discord.Client):
    """For each user in the database, fetch their Discord info from the guild and update DB (username, roles, join_date, is_member)."""
    guild = local_bot.get_guild(guild_id) or await local_bot.fetch_guild(guild_id)
    if guild is None:
        print(f"Guild {guild_id} not found.", file=__import__("sys").stderr)
        return

    rows = db_worker.fetchall("SELECT uid FROM USERS", ())
    uids = [row[0] for row in rows]
    updated = 0
    not_in_guild = []

    for uid in uids:
        member = guild.get_member(uid)
        if member is None:
            try:
                member = await guild.fetch_member(uid)
                await asyncio.sleep(0.2)  # gentle rate limit when hitting API
            except (discord.NotFound, discord.HTTPException):
                not_in_guild.append(uid)
                continue

        # Load existing row to preserve liable, visible, timeout, pov fields
        row = db_worker.fetchone("SELECT * FROM USERS WHERE uid = ?", (uid,))
        if not row:
            continue

        roles = ",".join([r.name for r in member.roles if r.name != "@everyone"])
        join_date = member.joined_at
        need_to_get = common.calculate_need_to_get(join_date) if join_date else (row[6] if len(row) > 6 else 45)

        user = datatypes.User(
            uuid=uid,
            server_username=member.display_name,
            global_username=member.global_name or getattr(member, "name", ""),
            liable=row[3] if len(row) > 3 else 1,
            visible=row[4] if len(row) > 4 else 1,
            timeout=row[5] if len(row) > 5 else None,
            need_to_get=need_to_get,
            is_member=1,
            join_date=join_date,
            roles=roles,
        )
        db_worker.add_user(user)
        updated += 1

    for uid in not_in_guild:
        db_worker.execute("UPDATE USERS SET is_member = 0 WHERE uid = ?", (uid,))

    print(f"Обновлено {updated} мемберов из {len(uids)} в БД (гильдия {guild.name}); не в гильдии: {len(not_in_guild)}")


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.default()
    intents.members = True

    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"bot ready as {bot.user}")
        await get_nicks(guild_id=int(os.getenv("DISCORD_GUILD_ID", "0")), local_bot=bot)
        await bot.close()

    bot.run(TOKEN)
