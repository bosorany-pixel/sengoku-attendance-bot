import os
import dotenv

# Load env file before any other local imports; otherwise e.g. monthly_results
# is imported via db_worker/datatypes and calls load_dotenv() (default .env),
# and with override=False our .env.erebor would not override those values.
env_file = os.getenv("ENV_FILE", ".env")
print(f"env file {env_file}")
dotenv.load_dotenv(env_file)

import discord
from discord.ext import commands
import src.db_worker as dbw
import src.datatypes as datatypes
import src.common as common


db_worker = dbw.DBWorker()


async def get_nicks(guild_id: int, local_bot: discord.Client):
    """Sync guild members with DB: add new Discord members, update existing, mark left members (is_member=0)."""
    guild = local_bot.get_guild(guild_id) or await local_bot.fetch_guild(guild_id)
    if guild is None:
        print(f"Guild {guild_id} not found.", file=__import__("sys").stderr)
        return

    rows = db_worker.fetchall("SELECT uid FROM USERS", ())
    uids_from_db = set(row[0] for row in rows)
    members_in_guild = set()
    updated = 0

    async for member in guild.fetch_members(limit=None):
        members_in_guild.add(member.id)
        row = db_worker.fetchone("SELECT * FROM USERS WHERE uid = ?", (member.id,))
        roles = ",".join([r.name for r in member.roles if r.name != "@everyone"])
        join_date = member.joined_at
        need_to_get = common.calculate_need_to_get(join_date) if join_date else (row[6] if row and len(row) > 6 else 45)

        user = datatypes.User(
            uuid=member.id,
            server_username=member.display_name,
            global_username=member.global_name or getattr(member, "name", ""),
            liable=row[3] if row and len(row) > 3 else 1,
            visible=row[4] if row and len(row) > 4 else 1,
            timeout=row[5] if row and len(row) > 5 else None,
            need_to_get=need_to_get,
            is_member=1,
            join_date=join_date,
            roles=roles,
        )
        db_worker.add_user(user)
        updated += 1

    not_in_guild = [uid for uid in uids_from_db if uid not in members_in_guild]
    for uid in not_in_guild:
        db_worker.execute("UPDATE USERS SET is_member = 0, roles='' WHERE uid = ?", (uid,))

    print(f"Обновлено {updated} мемберов в БД (гильдия {guild.name}); не в гильдии: {len(not_in_guild)}")


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.default()
    intents.members = True

    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"bot ready as {bot.user}")
        print(f'guild {int(os.getenv("DISCORD_GUILD_ID", "0"))}')
        await get_nicks(guild_id=int(os.getenv("DISCORD_GUILD_ID", "0")), local_bot=bot)
        await bot.close()

    bot.run(TOKEN)
