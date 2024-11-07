from dotenv import load_dotenv
import os
import requests
import threading    # для відстежування часу, тригер на час
from datetime import datetime, timezone
import json
import os
from bot import user_data


# load_dotenv()
#
# NOTION_DATABASE_TOKEN = os.getenv("NOTION_DATABASE_TOKEN")
# DATABASE_ID = os.getenv("DATABASE_ID")
# # TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
#
# # Початок роботи з Notion
# headers = {
#     'Authorization': 'Bearer ' + NOTION_DATABASE_TOKEN,
#     'Notion-Version': '2022-06-28',
#     'Content-Type': 'application/json',
# }

# "object": "page" - это название одной строки таблицы

# data: dict
def create_page():
    load_dotenv()

    NOTION_DATABASE_TOKEN = os.getenv("NOTION_DATABASE_TOKEN")
    DATABASE_ID = os.getenv("DATABASE_ID")
    # TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Початок роботи з Notion
    headers = {
        'Authorization': 'Bearer ' + NOTION_DATABASE_TOKEN,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }

    name = "Test name"
    greeting = "Test text"
    date_needed = datetime.now().astimezone(timezone.utc).isoformat()

    data = {
        "Ім'я/назва": {"title": [{"text": {"content": name}}]},
        "Текст привітання": {"rich_text": [{"text": {"content": greeting}}]},
        "Дата": {"date": {"start": date_needed, "end": None}}
    }

    url = f'https://api.notion.com/v1/pages'
    payload = {'parent': {'database_id': DATABASE_ID}, 'properties': data}

    res = requests.post(url, headers=headers, json=payload)
    print(res.status_code)


    # try:
    #     create_page()
    # except Exception as e:
    #     print(f"Помилка: {e}")

    return res


create_page()


# def get_pages():
#     url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
#     payload = {'page_size': 100}
#     response = requests.post(url, json=payload, headers=headers)
#     data = response.json()
#     with open ('data.json', 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)
#
#     if response.status_code != 200:
#         print(f"Ошибка: {response.status_code}")
#         print(response.json())  # Выводим ответ для отладки
#         return None
#
#     results = data['results']
#     return results
#
# # pages = get_pages()  # Запит на діставання json
#
# with open('data.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)
#
# if 'results' in data:
#     pages = data['results']
#     for page in pages:
#         props = page['properties']
#
#         if "Текст привітання" in props:
#             if len(props["Текст привітання"]["rich_text"]) > 0:
#                 congrad_text = props["Текст привітання"]["rich_text"][0]["text"]["content"]
#                 print(congrad_text)
#             else:
#                 print("Текст привітання пустой для одной из страниц.")
#         else:
#             print("Свойство 'Текст привітання' не найдено или пустое.")
#     else:
#         print("Ключ 'results' не найден в файле.")




