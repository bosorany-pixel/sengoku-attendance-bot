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

@bot.tree.command(name="add_payment", description="создать выплату")
@bot.tree.describe(
    payment="Сумма выплаты в миллионах, (например '22', '13.6', '32.1')"
)
async def add_payment(interaction: discord.Interaction, payment: str):
    try:
        payment = int(payment)
    except:
        await interaction.response.send_message("Что-то не так, проверь формат пожалуйста", ephemeral=True)
    
    msg = await interaction.channel.send(f"создана выплата {payment}кк. Кидайте скриншоты пачек в ветку В ТЕЧЕНИЕ ЧАСА (до {datetime.now(timezone.utc) + timedelta(hours=1)} utc)")
    await msg.create_thread("скриншоты пачек сюда")

if __name__ == "__main__":
    bot.run(TOKEN)