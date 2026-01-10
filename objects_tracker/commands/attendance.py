from objects_tracker.utils.ya_ocr import _get_names_from_image
import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
from objects_tracker.utils.data_store import load_allowed_roles
from src.db_worker import *
from src.datatypes import *

from objects_tracker.commands.on_message import add_consumer, remove_consumer
counter = 1000

db_worker = DBWorker()
att_threads: dict[int, datetime.datetime] = {}  # thread_id -> deadline_utc
att_tread_to_messages: dict[int, int] = {} # thread_id -> message_id

async def on_attendance_message(message: discord.Message):
    deadline = att_threads.get(message.channel.id)
    if not deadline:
        return
    now = datetime.datetime.now(timezone.utc)
    if now > deadline:
        att_threads.pop(message.channel.id, None)
        att_tread_to_messages.pop(message.channel.id, None)
        remove_consumer(message.channel.id)
        return
    if not message.attachments:
        return
    added_to = []
    for att in message.attachments:
        ct = att.content_type or ""
        if ct.startswith("image/"):
            names = await _get_names_from_image(att)
            for n in names:
                uid = db_worker.get_uid_by_name(n)
                if uid:
                    added_to.append(n)
                    db_worker.add_event_user_link(uid, att_tread_to_messages[message.channel.id])
    await message.add_reaction('✏️')
    if len(added_to) > 0:
        await message.reply(", ".join(added_to))
    else:
        await message.reply('Не вижу тут ников...')
    
@app_commands.command(name="create_attendance", description="создать посещение")
@app_commands.describe(att_name="Название контента, например 'zvz 10.01 12 utc'")
async def create_attendance(interaction: discord.Interaction, att_name: str):
    allowed_role_ids = load_allowed_roles(interaction.guild.id)
    if allowed_role_ids:
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in allowed_role_ids for role_id in user_role_ids):
            await interaction.response.send_message("У вас нет прав для добавления данных.", ephemeral=True)
            return
    await interaction.response.send_message("Сейчас создам", ephemeral=True)

    deadline = datetime.datetime.now(timezone.utc) + timedelta(hours=1)
    time_str = deadline.strftime("%Y-%m-%d %H:%M:%S")


    msg = await interaction.channel.send(
        f"👪 {att_name}.\n"
        f"😎 коллер {interaction.user.name}\n"
        f"📝 Кидайте скриншоты пачек в ветку В ТЕЧЕНИЕ ЧАСА (до {time_str} utc)".replace(",", " ")
    )
    thread = await msg.create_thread(name="скриншоты пачек сюда")
    ev = Event(
        message_id=msg.id,
        author=db_worker.get_user(interaction.user.id),
        message_text=att_name,
        disband=0,
        channel_id=interaction.channel.id,
        channel_name=interaction.channel.name,
        guild_id=interaction.guild.id,
        hidden=False,
        points=1
    )
    db_worker.add_event(ev)

    att_threads[thread.id] = deadline
    att_tread_to_messages[thread.id] = msg.id
    add_consumer(thread.id, on_attendance_message)