# Импортируйте библиотеку для кодирования в Base64
import requests
import base64
import json
import dotenv
dotenv.load_dotenv()
import os

# Создайте функцию, которая кодирует файл и возвращает результат.
def encode_file(file_path):
  with open(file_path, "rb") as fid:
    file_content = fid.read()
  return base64.b64encode(file_content).decode("utf-8")

data = {"mimeType": "jpg",
        "languageCodes": ["ru","en"],
        "content": encode_file('/home/sergei-scv/Downloads/test_ocr.jpg')}

url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

headers= {"Content-Type": "application/json",
          "Authorization": "Bearer {:s}".format(os.getenv("IAM_TOKEN")),
          "x-folder-id": "b1g9o81kme3o99o6bh0f",
          "x-data-logging-enabled": "true"}
  
w = requests.post(url=url, headers=headers, data=json.dumps(data))

with open("test.txt", 'w') as f:
    f.write(w.text)
    