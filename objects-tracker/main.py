import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)
import asyncio
import discord
from discord.ext import commands, tasks
import os
import json
from dotenv import load_dotenv

from commands import add_data, show_data, delete_data, set_allowed_roles
from commands.add_from_image import add_from_image
from tasks import cleanup_data

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not DISCORD_BOT_TOKEN:
    logging.error("DISCORD_BOT_TOKEN не задан в окружении")
    raise ValueError("Критическая ошибка: Токен бота Discord не найден в окружении.")
if not GOOGLE_API_KEY:
    logging.warning("GOOGLE_API_KEY не задан в окружении. Команда /add_from_image не будет работать.")

def save_server_names(bot_instance):
    """Собирает ID и имена всех серверов и сохраняет их в JSON."""
    server_info = {str(guild.id): guild.name for guild in bot_instance.guilds}
    try:
        with open("server_names.json", "w", encoding="utf-8") as f:
            json.dump(server_info, f, ensure_ascii=False, indent=4)
        logging.info(f"Сохранены имена для {len(server_info)} серверов.")
    except Exception as e:
        logging.error(f"Не удалось сохранить файл server_names.json: {e}")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    help_command=None
)

bot.tree.add_command(add_data.add_data)
bot.tree.add_command(show_data.show_data)
bot.tree.add_command(delete_data.delete_data)
bot.tree.add_command(set_allowed_roles.set_allowed_roles)
bot.tree.add_command(add_from_image)

@tasks.loop(minutes=1)
async def cleanup_data_loop():
    await cleanup_data.cleanup_data(bot)

@bot.tree.command(name="ping", description="ping")
async def ping(interaction: discord.Interaction):
    logging.info("PING received")
    await interaction.response.send_message("pong", ephemeral=True)


@bot.event
async def on_ready():
    logging.info(f'Bot {bot.user} is ready!')
    print(f'Bot {bot.user} is ready!')
    print(DISCORD_BOT_TOKEN[:10])
    
    save_server_names(bot)

    if not cleanup_data_loop.is_running():
        cleanup_data_loop.start()

    logging.info("Начинаю глобальную синхронизацию команд...")
    try:
        synced = await bot.tree.sync()
        logging.info(f"Глобально синхронизировано {len(synced)} команд")
    except Exception as e:
        logging.error(f"Ошибка при синхронизации команд: {e}")

@bot.event
async def on_guild_join(guild):
    """Событие, когда бота добавляют на новый сервер."""
    logging.info(f"Бот добавлен на сервер: {guild.name} ({guild.id})")
    save_server_names(bot)

@bot.event
async def on_guild_remove(guild):
    """Событие, когда бота удаляют с сервера."""
    logging.info(f"Бот удален с сервера: {guild.name} ({guild.id})")
    save_server_names(bot)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    logging.exception("App command error", exc_info=error)
    if interaction.response.is_done():
        await interaction.followup.send(f"Ошибка: {error}", ephemeral=True)
    else:
        await interaction.response.send_message(f"Ошибка: {error}", ephemeral=True)


async def main():
    try:
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)