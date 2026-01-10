import datetime
import inspect
import os
from typing import Awaitable, Callable, Dict, Optional, Union

import discord
from src.guild import get_nicks

Consumer = Callable[[discord.Message], Union[None, Awaitable[None]]]

thread_consumer: Dict[int, Consumer] = {}
last_update = datetime.datetime.now(datetime.timezone.utc)


async def on_message(message: discord.Message, bot: discord.Client):
    global last_update
    now = datetime.datetime.now(datetime.timezone.utc)
    if now - last_update > datetime.timedelta(minutes=10):
        try:
            await get_nicks(guild_id=os.getenv("DISCORD_GUILD_ID"), local_bot=bot)
        finally:
            last_update = now

    if message.author.bot:
        return

    if not isinstance(message.channel, discord.Thread):
        return

    if message.channel.archived or message.channel.locked:
        thread_consumer.pop(message.channel.id, None)
        return

    consumer = thread_consumer.get(message.channel.id)
    if not consumer:
        return

    try:
        res = consumer(message)
        if inspect.isawaitable(res):
            await res
        # await message.add_reaction("✅")
    except Exception:
        try:
            await message.add_reaction("❌")
        finally:
            raise


def add_consumer(thread_id: int, func: Consumer):
    if thread_id in thread_consumer:
        raise RuntimeError("consumer already exists")
    thread_consumer[thread_id] = func


def remove_consumer(thread_id: int) -> None:
    thread_consumer.pop(thread_id, None)


def clear_consumers() -> None:
    thread_consumer.clear()
