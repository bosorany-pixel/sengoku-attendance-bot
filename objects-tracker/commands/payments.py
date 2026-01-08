import logging
import discord
from discord import app_commands
import json
from datetime import datetime, timezone, timedelta

@app_commands.command(name="add_payment", description="создать выплату")
@app_commands.describe(
    payment="Сумма выплаты в миллионах, (например '22', '13.6', '32.1')"
)
async def add_payment(interaction: discord.Interaction, payment: str):
    try:
        payment = int(payment)
    except:
        await interaction.response.send_message("Что-то не так, проверь формат пожалуйста", ephemeral=True)
        return
    await interaction.response.send_message("Сейчас создам", ephemeral=True)
    msg = await interaction.channel.send(f"создана выплата {payment}кк. Кидайте скриншоты пачек в ветку В ТЕЧЕНИЕ ЧАСА (до {datetime.now(timezone.utc) + timedelta(hours=1)} utc)")
    await msg.create_thread(name="скриншоты пачек сюда")
