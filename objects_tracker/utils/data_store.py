import asyncio
import json
import os
import logging
from typing import Dict, List, Any

DATA_DIR = "bot_data"
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
        logging.info(f"Создана директория для данных: {DATA_DIR}")
    except OSError as e:
        logging.error(f"Не удалось создать директорию для данных {DATA_DIR}: {e}")
        DATA_DIR = "."


MESSAGES_FILE_PATH = os.path.join(DATA_DIR, "show_data_messages.json")

def load_show_data_messages() -> Dict[int, int]:
    """Загружает ID отслеживаемых сообщений из файла."""
    try:
        with open(MESSAGES_FILE_PATH, "r", encoding="utf-8") as f:
            return {int(k): v for k, v in json.load(f).items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_show_data_messages(messages_dict: Dict[int, int]):
    """Сохраняет ID отслеживаемых сообщений в файл."""
    try:
        with open(MESSAGES_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(messages_dict, f, indent=4)
    except IOError as e:
        logging.error(f"Ошибка при сохранении файла сообщений: {e}")


data_lock = asyncio.Lock()
show_data_messages: Dict[int, int] = load_show_data_messages()


def get_data_file_path(guild_id: Any) -> str:
    return os.path.join(DATA_DIR, f"data_{str(guild_id)}.json")

def load_data(guild_id: Any) -> Dict[str, List[Any]]:
    data_file = get_data_file_path(guild_id)
    default_structure = {"items": [], "allowed_roles": []}
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default_structure
            data = json.loads(content)
            if not isinstance(data, dict) or "items" not in data or "allowed_roles" not in data:
                logging.warning(f"Файл данных {data_file} имеет некорректную структуру. Используется структура по умолчанию.")
                return default_structure
            return data
    except FileNotFoundError:
        return default_structure
    except json.JSONDecodeError:
        logging.error(f"Ошибка декодирования JSON в файле {data_file}. Используется структура по умолчанию.")
        return default_structure
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из {data_file}: {e}. Используется структура по умолчанию.")
        return default_structure

def save_data(guild_id: Any, data_items: List[Dict[str, Any]], allowed_roles: List[int]):
    data_file = get_data_file_path(guild_id)
    data_to_save = {"items": data_items, "allowed_roles": allowed_roles}
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
    except IOError as e:
        logging.error(f"Ошибка ввода-вывода при сохранении данных в {data_file}: {e}")

def save_allowed_roles(guild_id: Any, allowed_role_ids: List[int]):
    current_data = load_data(guild_id)
    save_data(guild_id, current_data.get("items", []), allowed_role_ids)
    logging.info(f"Разрешенные роли для guild {guild_id} обновлены.")

def load_allowed_roles(guild_id: Any) -> List[int]:
    data = load_data(guild_id)
    return data.get("allowed_roles", [])