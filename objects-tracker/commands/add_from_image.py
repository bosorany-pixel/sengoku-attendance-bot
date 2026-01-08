import discord
import base64
import datetime
from discord import app_commands
import logging
import os
import json
import io
import os
import dotenv
import requests
import re
dotenv.load_dotenv()

if os.getenv('GENAI_SOL') in {"true", "yes", "y"}:
    import google.generativeai as genai
from PIL import Image

from .add_data import _internal_add_item

api_key = os.getenv("GOOGLE_API_KEY")
gemini_configured = bool(api_key)


@app_commands.command(name="add_from_image",
                      description="Добавляет объект, распознав данные и ВИД с изображения (Gemini / yandex ocr).")
@app_commands.describe(image="Изображение (скриншот) с данными об объекте")
async def add_from_image(interaction: discord.Interaction, image: discord.Attachment):
    logging.info("got an image")
    if os.getenv('GENAI_SOL') in {"true", "yes", "y"}:
        pass
    else:
        image_bytes = await image.read()
        img = Image.open(io.BytesIO(image_bytes))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()
        content = base64.b64encode(image_bytes).decode("ascii")

        # Create the JSON body
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
            await interaction.response.send_message(
                        f"Ошибка api {w.status_code}: \n`{w.text}`",
                        ephemeral=True
                    )
            return
        if len(objects_text) == 0:
            await interaction.response.send_message(w.text, ephemeral=True)
        if objects_text[-1] == '\n':
            objects_text = objects_text[:-1]
        obj_name = objects_text.split("\n")[0]
        obj_location = objects_text.split("\n")[-1]
        hours_match = re.search(r'(\d+) (ч|h)', objects_text)
        minutes_match = re.search(r'(\d+) (m|м)', objects_text)
        hours = int(hours_match.group(1))
        minutes = int(minutes_match.group(1))
        
        # Get the current date and time
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Create a timedelta object with the extracted hours and minutes
        time_delta = datetime.timedelta(hours=hours, minutes=minutes)
        
        # Add the timedelta to the current time
        obj_time = current_time + time_delta
        error_message = await _internal_add_item(interaction, str(obj_time), obj_location, object_name=obj_name)

        if error_message:
            await interaction.response.send_message(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(
                        f"✅ Распознано и добавлено:\n"
                        f"**Объект:** {obj_name}\n"
                        f"**Локация:** {obj_location}\n"
                        f"**Время:** {obj_time}",
                        ephemeral=True
                    )