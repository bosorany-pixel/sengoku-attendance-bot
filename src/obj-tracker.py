import os
import sys
import discord
from datetime import datetime, timedelta, timezone
import discord.ext.commands
import dotenv
import datatypes
import common
import CONSTANTS
import db_worker as dbw
import discord.ext
import logger
import pandas as pd
from io import BytesIO
dotenv.load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
bot = discord.ext.commands.Bot(intents=intents, command_prefix='!')

db_worker = dbw.DBWorker()
lgr = logger.get_logger("obj-tracker")

@bot.event
async def on_ready():
    for GUILD_ID in CONSTANTS.GUILD_IDS:
        guild_obj = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        try:
            await bot.tree.sync(guild=guild_obj)
        except Exception as e:
            lgr.error(f"error with {GUILD_ID}: {e}")
        else:
            lgr.info(f"guild {GUILD_ID} added")

    print(f"Logged in as {bot.user} (id={bot.user.id})")
    ch = bot.get_channel(1427006146203615332)
    await ch.send("hiiii")

@bot.tree.command(name="show", description="Показать, сколько изображений сохранено")
async def show(interaction: discord.Interaction):
    await interaction.response.send_message("только на сервере")

if __name__ == "__main__":
    bot.run(TOKEN)