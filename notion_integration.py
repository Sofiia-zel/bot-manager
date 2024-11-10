from dotenv import load_dotenv
import requests
import threading    # для відстежування часу, тригер на час
from datetime import datetime, timezone, timedelta
import os


# "object": "page" - это название одной строки таблицы

# Функція для того, щоб не повторювати токени та хедерси у кожній наступній функції
def get_notion_headers():
    load_dotenv()
    NOTION_DATABASE_TOKEN = os.getenv("NOTION_DATABASE_TOKEN")
    DATABASE_ID = os.getenv("DATABASE_ID")
    headers = {
        'Authorization': 'Bearer ' + NOTION_DATABASE_TOKEN,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }
    return headers, DATABASE_ID


def create_page(data: dict):
    headers, DATABASE_ID = get_notion_headers()
    url = f'https://api.notion.com/v1/pages'
    payload = {'parent': {'database_id': DATABASE_ID}, 'properties': data}
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("Страница успешно создана в Notion.")
    else:
        print(f"Ошибка {res.status_code}: {res.text}")
    return res


def show_people_names():
    headers, DATABASE_ID = get_notion_headers()
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    payload = {'page_size': 100}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if response.status_code != 200:
        return f"Ошибка при запросе к API: {response.status_code}"

    if 'results' not in data:
        return "Ключ 'results' не найден в файле."

    names = []  # Список для сбора всех имен и названий событий

    pages = data['results']
    for page in pages:
        props = page['properties']
        if "Ім'я/назва" in props:
            if len(props["Ім'я/назва"]["title"]) > 0:
                name = props["Ім'я/назва"]["title"][0]["text"]["content"]
                names.append(name)  # Добавляем имя или название события в список
            else:
                names.append("Назва пуста.")
        else:
            names.append("Свойство 'Ім'я/назва' не найдено или пустое.")
    # Объединяем все имена в одну строку с новой строкой между каждым именем
    return "\n".join(names)


def show_existing_events():
    headers, DATABASE_ID = get_notion_headers()
    url = f'https://api.notion.com/v1/databases/{DATABASE_ID}/query'
    payload = {'page_size': 100}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if response.status_code != 200:
        return f"Ошибка при запросе к API: {response.status_code}"

    if 'results' not in data:
        return "Ключ 'results' не найден в файле."

    events_dict = {}  # Словарь для сбора информации о событиях
    event_number = 1  # Начинаем с 1

    pages = data['results']
    for page in pages:
        props = page['properties']

        # Инициализируем структуру для одного события
        event_data = {}

        # Извлекаем значение "Ім'я/назва"
        if "Ім'я/назва" in props and len(props["Ім'я/назва"]["title"]) > 0:
            event_data["Ім'я/назва"] = props["Ім'я/назва"]["title"][0]["text"]["content"]
        else:
            event_data["Ім'я/назва"] = "Назва пуста."

        # Извлекаем значение "Дата"
        if "Дата" in props and "date" in props["Дата"] and props["Дата"]["date"] is not None:
            full_date = props["Дата"]["date"]["start"]
            # Обрезаем строку до символа 'T', используем форматирование
            event_data["Дата"] = datetime.fromisoformat(full_date).strftime('%d-%m-%Y')
        else:
            event_data["Дата"] = "Дата не указана."

        # Извлекаем значение "Текст привітання"
        if "Текст привітання" in props and len(props["Текст привітання"]["rich_text"]) > 0:
            event_data["Текст привітання"] = props["Текст привітання"]["rich_text"][0]["text"]["content"]
        else:
            event_data["Текст привітання"] = "Привітання відсутнє."

        events_dict[event_number] = event_data
        event_number += 1  # Увеличиваем номер для следующего события

    return events_dict



# тренировка
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
#         # print(response.json())  # Выводим ответ для отладки
#         return None
#
#     results = data['results']
#     return results
#
#
# pages = get_pages()  # Запит на діставання json
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




