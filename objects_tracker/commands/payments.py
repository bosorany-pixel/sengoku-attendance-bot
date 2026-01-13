import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
from objects_tracker.utils.data_store import load_allowed_roles
from src.db_worker import *
from src.datatypes import *
from objects_tracker.commands.on_message import add_consumer, remove_consumer
from objects_tracker.utils.ya_ocr import _get_names_from_image

db_worker = DBWorker()
payment_threads: dict[int, datetime.datetime] = {}  # thread_id -> deadline_utc
payment_tread_to_messages: dict[int, int] = {} # thread_id -> payment_id

def _pay_member(payment: float, username: str, msg_id: int, ch_id: int, guild_id: int) -> str:
    uid = db_worker.get_uid_by_name(username)
    if not uid:
        return "bad username"
    pm = Payment(payment, msg_id, ch_id, guild_id)
    db_worker.add_payment(pm)
    db_worker.link_user_to_payment(uid, msg_id)
    return None

async def on_payment_message(message: discord.Message):
    deadline = payment_threads.get(message.channel.id)
    if not deadline:
        return
    now = datetime.datetime.now(timezone.utc)
    if now > deadline:
        payment_threads.pop(message.channel.id, None)
        payment_tread_to_messages.pop(message.channel.id, None)
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
                    db_worker.link_user_to_payment(uid, payment_tread_to_messages[message.channel.id])
    await message.add_reaction('💵')
    await message.reply(", ".join(added_to))



@app_commands.command(name="create_payment", description="создать выплату")
@app_commands.describe(payment="Сумма выплаты (например '22000000', '13600000', '32100000')")
async def create_payment(interaction: discord.Interaction, payment: str):
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

    payment_threads[thread.id] = deadline
    payment_tread_to_messages[thread.id] = msg.id
    add_consumer(thread.id, on_payment_message)


@app_commands.command(name="add_to_payment", description="добавить мембера в выплату. можно использовать только в ветке выплаты, в которую мембера не добавило.")
@app_commands.describe(
    username="Ник мембера, как в дискорде (например 'kKokSs (не кокос)')"
)
async def add_to_payment(interaction: discord.Interaction, username: str):
    allowed_role_ids = load_allowed_roles(interaction.guild.id, "core_roles")
    if allowed_role_ids:
        user_role_ids = [role.id for role in interaction.user.roles]
        if not any(role_id in allowed_role_ids for role_id in user_role_ids):
            await interaction.response.send_message("У вас нет прав для добавления данных.", ephemeral=True)
            return
    uid = db_worker.get_uid_by_name(username)
    if uid and interaction.channel.id in payment_tread_to_messages:
        db_worker.add_event_user_link(uid, payment_tread_to_messages[interaction.channel.id])
        await interaction.response.send_message(f"Добавил {username} в выплату ✅")
    else:
        await interaction.response.send_message("Кажется, ветка записи уже закрыта", ephemeral=True)


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


@app_commands.command(name="top_balance", description="топ балансов гильдии")
@app_commands.describe(
    top_n="топ сколько вам надо (например '3', '5' и тд)"
)
async def top_balance(interaction: discord.Interaction, top_n: str):
    try:
        top_n = int(top_n)
    except Exception as e:
        await interaction.response.send_message(str(e), ephemeral=True)
    if top_n > 20:
        await interaction.response.send_message("НЕМАЛО", ephemeral=True)
    await interaction.response.send_message(
        format_sqlite_rows(db_worker.get_top_users(top_n))
    )


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
