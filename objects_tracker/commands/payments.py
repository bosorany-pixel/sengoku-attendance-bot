from PIL import Image
import logging
import requests
import discord
from discord import app_commands
import json
from datetime import datetime, timezone, timedelta
from objects_tracker.utils.data_store import load_allowed_roles
import io
import base64
from src.db_worker import *
from src.datatypes import *
from src.guild import get_nicks
counter = 1000

db_worker = DBWorker()
active_threads: dict[int, datetime.datetime] = {}  # thread_id -> deadline_utc
active_threads_messages: dict[int, int] = {} # thread_id -> payment_id

async def _get_names_from_image(image: discord.Attachment) -> list:
    image_bytes = await image.read()
    img = Image.open(io.BytesIO(image_bytes))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    image_bytes = buffered.getvalue()
    content = base64.b64encode(image_bytes).decode("ascii")
    body = {
            "mimeType": "jpg",
            "languageCodes": ["ru", "en"],
            "content": content
        }

    headers= {"Content-Type": "application/json",
        "Authorization": "Api-Key {:s}".format(os.getenv("YANDEX_API_KEY")),
        "x-folder-id": "b1g9o81kme3o99o6bh0f",
        "x-data-logging-enabled": "true"}
    
    w = requests.post(
        url="https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText", 
        headers=headers,
        data=json.dumps(body)
    )
    objects_text = ''
    try:
        if 'result' in dict(json.loads(w.text)):
            objects_text = dict(json.loads(w.text))['result']['textAnnotation']['fullText']
        else:
            objects_text = ""
    except Exception as e:
            logging.error(str(e))
            return
    return objects_text.split('\n')


def _pay_member(payment: float, username: str, msg_id: int, ch_id: int, guild_id: int) -> str:
    uid = db_worker.get_uid_by_name(username)
    if not uid:
        return "bad username"
    pm = Payment(payment, msg_id, ch_id, guild_id)
    db_worker.add_payment(pm)
    db_worker.link_user_to_payment(uid, msg_id)
    return None

async def on_message(message: discord.Message):
    global counter
    counter += 1
    if counter >= 1000:
        await get_nicks(guild_id=os.getenv("DISCORD_GUILD_ID"))
        counter = 0
    if message.author.bot:
        return
    if not isinstance(message.channel, discord.Thread):
        return
    deadline = active_threads.get(message.channel.id)
    if not deadline:
        return
    now = datetime.datetime.now(timezone.utc)
    if now > deadline:
        active_threads.pop(message.channel.id, None)
        active_threads_messages.pop(message.channel.id, None)
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
                    db_worker.link_user_to_payment(uid, active_threads_messages[message.channel.id])
    await message.add_reaction('✅')



@app_commands.command(name="add_payment", description="создать выплату")
@app_commands.describe(payment="Сумма выплаты (например '22000000', '13600000', '32100000')")
async def add_payment(interaction: discord.Interaction, payment: str):
    allowed_role_ids = load_allowed_roles(interaction.guild.id)
    if allowed_role_ids:
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in allowed_role_ids for role_id in user_role_ids):
            await interaction.response.send_message("У вас нет прав для добавления данных.", ephemeral=True)
            return
    try:
        payment = int(payment)
    except:
        await interaction.response.send_message("Что-то не так, проверь формат пожалуйста", ephemeral=True)
        return

    await interaction.response.send_message("Сейчас создам", ephemeral=True)

    deadline = datetime.datetime.now(timezone.utc) + timedelta(hours=1)
    time_str = deadline.strftime("%Y-%m-%d %H:%M:%S")


    msg = await interaction.channel.send(
        f"💰 Cоздана выплата {payment:,.2f} серебра.\n"
        f"📝 Кидайте скриншоты пачек в ветку В ТЕЧЕНИЕ ЧАСА (до {time_str} utc)".replace(",", " ")
    )
    thread = await msg.create_thread(name="скриншоты пачек сюда")
    pm = datatypes.Payment(payment, msg.id, msg.channel.id, msg.guild.id)
    db_worker.add_payment(pm)

    active_threads[thread.id] = deadline
    active_threads_messages[thread.id] = msg.id

@app_commands.command(name="inc_payment", description="увеличить сумму в табличке для мембера")
@app_commands.describe(
    payment="Сумма выплаты (например '10100000', '3000000' и тд)",
    username="Ник мембера, как в дискорде (например 'kKokSs (не кокос)')"
)
async def inc_payment(interaction: discord.Interaction, payment: str, username: str):
    allowed_role_ids = load_allowed_roles(interaction.guild.id)
    if allowed_role_ids:
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in allowed_role_ids for role_id in user_role_ids):
            await interaction.response.send_message("У вас нет прав для добавления данных.", ephemeral=True)
            return
    try:
        payment = float(payment)
    except:
        await interaction.response.send_message("Что-то не так, проверь формат пожалуйста", ephemeral=True)
        return
    r = _pay_member(float(payment), username, interaction.id, interaction.channel.id, interaction.guild.id)
    if not r:
        await interaction.response.send_message(f"Добавил {username} {payment:,.2f} серебра ✅".replace(",", " "))
    else:
        await interaction.response.send_message(f"Что-то пошло не так :с ❌")
    

@app_commands.command(name="dec_payment", description="уменьшить сумму в табличке для мембера")
@app_commands.describe(
    payment="Сумма (например '10100000', '3000000' и тд)",
    username="Ник мембера, как в дискорде (например 'kKokSs (не кокос)')"
)
async def dec_payment(interaction: discord.Interaction, payment: str, username: str):
    allowed_role_ids = load_allowed_roles(interaction.guild.id)
    if allowed_role_ids:
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in allowed_role_ids for role_id in user_role_ids):
            await interaction.response.send_message("У вас нет прав для добавления данных.", ephemeral=True)
            return
    try:
        payment = -1 * float(payment)
    except Exception as e:
        await interaction.response.send_message(f"Что-то не так, проверь формат пожалуйста\n{e}", ephemeral=True)
        return
    r = _pay_member(float(payment), username, interaction.id, interaction.channel.id, interaction.guild.id)
    if not r:
        await interaction.response.send_message(f"Вычел {username} {payment:,.2f} серебра ✅".replace(",", " "))
    else:
        await interaction.response.send_message(f"Что-то пошло не так :с ❌")


@app_commands.command(name="get_balance", description="посмотреть баланс мембера")
@app_commands.describe(
    username="Ник мембера, как в дискорде (например 'kKokSs (не кокос)')"
)
async def get_balance(interaction: discord.Interaction, username: str):
    uid = db_worker.get_uid_by_name(username)
    if not uid:
        await interaction.response.send_message("Что-то не так, проверь ник пожалуйста", ephemeral=True)
        return
    await interaction.response.send_message(f"сумма выплаты для {username} = {db_worker.get_balance(uid):,.2f} серебра".replace(",", " "))

@inc_payment.autocomplete("username")
async def uname_pay_autocomplete(interaction: discord.Interaction, current: str):
    current_lower = current.lower()
    choices = [
        app_commands.Choice(name=uname, value=uname)
        for uname in db_worker.get_server_names()
        if current_lower in uname.lower()
    ]
    choices.sort(key=lambda c: (not c.name.lower().startswith(current_lower), c.name.lower()))
    return choices[:25]

@dec_payment.autocomplete("username")
async def uname_fine_autocomplete(interaction: discord.Interaction, current: str):
    current_lower = current.lower()
    choices = [
        app_commands.Choice(name=uname, value=uname)
        for uname in db_worker.get_server_names()
        if current_lower in uname.lower()
    ]
    choices.sort(key=lambda c: (not c.name.lower().startswith(current_lower), c.name.lower()))
    return choices[:25]

@get_balance.autocomplete("username")
async def uname_get_autocomplete(interaction: discord.Interaction, current: str):
    current_lower = current.lower()
    choices = [
        app_commands.Choice(name=uname, value=uname)
        for uname in db_worker.get_server_names()
        if current_lower in uname.lower()
    ]
    choices.sort(key=lambda c: (not c.name.lower().startswith(current_lower), c.name.lower()))
    return choices[:25]
