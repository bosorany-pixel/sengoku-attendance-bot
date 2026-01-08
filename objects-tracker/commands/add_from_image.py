import discord
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
        if not gemini_configured:
            await interaction.response.send_message("Ошибка: API для Gemini не сконфигурирован (нет GOOGLE_API_KEY).",
                                                    ephemeral=True)
            return

        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.response.send_message("Ошибка: Прикрепленный файл не является изображением.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')

            image_bytes = await image.read()
            img = Image.open(io.BytesIO(image_bytes))

            prompt = [
                """
                Ты — эксперт по анализу игровых скриншотов из игры Albion Online. Твоя задача — извлечь из изображения данные об объекте и классифицировать его.

                КЛАССИФИКАЦИЯ ОБЪЕКТОВ:
                1. Если в названии есть слова типа:
                - "волокн(о|а)" или "fiber" -> тип "Ткань"
                - "шкур(а|ы)" или "skin" -> тип "Кожа" 
                - "руд(а|ы)" или "ore" -> тип "Руда"
                - "древесин(а|ы)" или "wood" -> тип "Дерево"
                - "вихр(ь|я)" или "vortex" -> тип "Вихрь"
                - "сил(ы,а) или "anomaly" -> тип "Сфера"
                
                2. Для объектов с тировыми обозначениями (Tier 8.4, T8.4, Bolca 8. kademe 4 и т.п.):
                - Добавь префикс тира к типу: "8.4 Ткань", "8.4 Руда" и т.д.

                3. Для "Вихрь" - ОПРЕДЕЛЕНИЕ ЦВЕТА:
                Силовой вихрь выглядит как КРИСТАЛЛ с вращающимися лентами/полосками вокруг.
                Определи ЦВЕТ КРИСТАЛЛА (не лент!):
                - ЖЕЛТЫЙ или ЗОЛОТОЙ кристалл -> "Золотой вихрь"
                - ФИОЛЕТОВЫЙ кристалл -> "Фиолетовый вихрь"  
                - СИНИЙ кристалл -> "Синий вихрь"
                - ЗЕЛЕНЫЙ кристалл -> "Зеленый вихрь"
                
                4. Для сфера - ОПРЕДЕЛЕНИЕ ЦВЕТА:
                Аномамалия силы выглядит как СФЕРА определёного цвета.
                Определи ЦВЕТ СФЕРЫ :
                - ЖЕЛТЫЙ или ЗОЛОТОЙ сфера -> "Золотая сфера"
                - ФИОЛЕТОВЫЙ сфера -> "Фиолетовая сфера"  
                - СИНИЙ сфера -> "Синняя сфера"
                - ЗЕЛЕНЫЙ сфера -> "Зеленая сфера"

                ИЗВЛЕКАЕМЫЕ ДАННЫЕ:
                1. 'location': Название локации (оставь как есть)
                2. 'object_type': Классифицированный тип объекта (см. правила выше)
                3. 'time_str': Время до появления объекта.
                - Внимательно определи числа и их единицы времени (часы, минуты, секунды) на любом языке.
                - **Твоя главная задача — вернуть это время в виде строки на РУССКОМ языке.**
                - Используй следующие сокращения: 'ч' для часов, 'м' для минут, 'с' для секунд.               
                - **ПРИМЕРЫ ПРЕОБРАЗОВАНИЯ:**
                    - Если на картинке "Unlocks In: 30 m 19 s" -> верни "30м 19с".
                    - Если на картинке "Откроется через: 1 h 5 m" -> верни "1ч 5м".
                    - Если на картинке "Appears in 25 minutes" -> верни "25м".
                    - Если на картинке "45s" -> верни "45с".

                ПРИМЕРЫ:
                - "Растение с большим количеством волокна 8.4 тира" -> "8.4 Ткань"
                - "A plant with plenty of Tier 8.4 fiber" -> "8.4 Ткань"  
                - "Силовой вихрь" с ФИОЛЕТОВЫМ кристаллом -> "Фиолетовый вихрь"
                - "Жила с рудой" -> "Руда"

                ВАЖНО:
                - Всегда смотри на ЦВЕТ КРИСТАЛЛА, а не лент вокруг него
                - Используй ТОЛЬКО эти 4 цвета: Золотой, Фиолетовый, Синий, Зеленый
                - Если не можешь определить цвет -> верни "Силовой вихрь"

                Верни ТОЛЬКО JSON:
                {
                "location": "название локации",
                "object_type": "классифицированный тип",
                "time_str": "время"
                }
                """,
                img
            ]

            response = await interaction.client.loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt, generation_config={"temperature": 0.0})
            )

            response_content = response.text
            logging.info(f"Ответ от Gemini: {response_content}")

            # Обработка ответа
            try:
                if response_content.startswith("```json"):
                    response_content = response_content.strip("```json\n").strip("`\n")

                api_data = json.loads(response_content)

                location = api_data.get("location")
                object_type = api_data.get("object_type")
                time_str = api_data.get("time_str")


                if not all([location, object_type, time_str]):
                    await interaction.followup.send(
                        f"Не удалось распознать обязательные данные. Модель вернула: \n`{response_content}`",
                        ephemeral=True
                    )
                    return

                error_message = await _internal_add_item(interaction, time_str=str(time_str), location=location, object_name=object_type)

                if error_message:
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.followup.send(
                        f"✅ Распознано и добавлено:\n"
                        f"**Объект:** {object_type}\n"
                        f"**Локация:** {location}\n"
                        f"**Время:** {time_str}",
                        ephemeral=True
                    )

            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Не удалось распарсить JSON из ответа Gemini: {e}. Ответ: {response_content}")
                await interaction.followup.send("Ошибка: Не удалось обработать ответ от сервиса распознавания.",
                                                ephemeral=True)

        except Exception as e:
            logging.error(f"Ошибка в команде add_from_image: {e}", exc_info=True)
            await interaction.followup.send("Произошла критическая ошибка при обработке изображения.", ephemeral=True)
    else:
        image_bytes = await image.read()
        img = Image.open(io.BytesIO(image_bytes))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()
        content = image_bytes.decode('latin1')  # Decode bytes to string for JSON

        # Create the JSON body
        body = {
            "mimeType": "jpg",
            "languageCodes": ["ru", "en"],
            "content": content
        }

        headers= {"Content-Type": "application/json",
          "Authorization": "Bearer {:s}".format(os.getenv("IAM_TOKEN")),
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
                raise KeyError
        except Exception as e:
            logging.error(str(e))
            await interaction.followup.send(
                        f"Ошибка api {w.status_code}: \n`{w.text}`",
                        ephemeral=True
                    )
            return

        if objects_text[-1] == '\n':
            objects_text = objects_text[:-1]
        obj_name = objects_text.split("\n")[0]
        obj_location = objects_text.split("\n")[-1]
        hours_match = re.search(r'(\d+) (ч|h)', objects_text)
        minutes_match = re.search(r'(\d+) (m|м)', objects_text)
        hours = int(hours_match.group(0))
        minutes = int(minutes_match.group(0))
        
        # Get the current date and time
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Create a timedelta object with the extracted hours and minutes
        time_delta = datetime.timedelta(hours=hours, minutes=minutes)
        
        # Add the timedelta to the current time
        obj_time = current_time + time_delta
        error_message = await _internal_add_item(interaction, str(obj_time), obj_location, object_type)

        if error_message:
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.followup.send(
                        f"✅ Распознано и добавлено:\n"
                        f"**Объект:** {obj_name}\n"
                        f"**Локация:** {obj_location}\n"
                        f"**Время:** {obj_time}",
                        ephemeral=True
                    )