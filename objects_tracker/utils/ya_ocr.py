import discord
from PIL import Image
import io
import base64
import requests
import json
import logging
import os
import dotenv
dotenv.load_dotenv()

async def _get_names_from_image(image: discord.Attachment) -> list:
    image_bytes = await image.read()
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode == 'RGBA':
        img = img.convert('RGB')
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
    print(f"recognized text {objects_text}")
    return objects_text.split('\n')

