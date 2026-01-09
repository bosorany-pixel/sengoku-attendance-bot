import asyncio
import os
import discord
from discord.ext import commands
import dotenv
import src.db_worker as dbw
import src.datatypes as datatypes
import src.common as common
dotenv.load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
db_worker = dbw.DBWorker()

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)

async def get_nicks(guild_id: int):
    guild = bot.get_guild(guild_id) or await bot.fetch_guild(guild_id)

    count = 0
    async for m in guild.fetch_members(limit=None):
        count += 1

        user = db_worker.get_user(m.id)
        roles = ",".join([r.name for r in m.roles if r.name != "@everyone"])
        join_date = m.joined_at

        if user:
            user.global_username = m.global_name
            user.server_username = m.display_name
            user.join_date = join_date
            user.roles = roles
            user.need_to_get = common.calculate_need_to_get(join_date)
        else:
            user = datatypes.User(
                m.id,
                m.display_name,
                m.global_name,
                join_date=join_date,
                need_to_get=common.calculate_need_to_get(join_date),
                roles=roles,
            )

        db_worker.add_user(user)

    print(f"{count} мемберов в гильдии {guild.name}")


@bot.event
async def on_ready():
    print(f"bot ready as {bot.user}")
    await get_nicks(guild_id=os.getenv("DISCORD_GUILD_ID"))
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
