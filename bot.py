import telebot
from telebot import types, TeleBot
from dotenv import load_dotenv
import os
import time
import threading
from datetime import datetime, timezone, timedelta, tzinfo
from notion_integration import (create_page, show_people_names, show_existing_events,
                                find_page_id_by_name, delete_page, update_page)
import pytz
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = TeleBot(TELEGRAM_TOKEN)

# Хранение данных о новом событии
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    add_event_btn = types.KeyboardButton("➕ Додати нову подію")
    show_events_btn = types.KeyboardButton("🗒 Показати події")
    update_btn = types.KeyboardButton("🔄 Оновити подію")
    delete_btn = types.KeyboardButton("❌ Видалити подію")
    show_people_btn = types.KeyboardButton("👥 Показати та назви подій")
    calendar_btn = types.KeyboardButton("📅 Календар подій")
    keyboard.add(add_event_btn, show_events_btn, update_btn, delete_btn, show_people_btn, calendar_btn)
    bot.send_message(message.chat.id, "Вас вітає бот-менеджер! Виберіть необхідну функцію з переліку.", reply_markup=keyboard)


# ОБРОБКА СТВОРЕННЯ НОВОЇ ПОДІЇ, перехоплення потрібної інформації від користувача
@bot.message_handler(func=lambda message: message.text == "➕ Додати нову подію")
def add_new_event(message):
    msg = bot.send_message(message.chat.id, "Введіть ім'я/назву події або введіть 'відміна':")

    def name_or_cancel_step(name_message):
        if name_message.text.lower() == "відміна":
            # Если введено "відміна", показываем главное меню и подтверждаем отмену
            bot.send_message(message.chat.id, "Відміну підтверджено!")
            start(name_message)
        # TODO реалізувати перевірку на наявність введеної користувачем назви у базі
        # elif name_message.text.lower() in show_people_names():
        #     markup = types.InlineKeyboardMarkup()
        #     markup.add(types.InlineKeyboardButton("Оновити існуюче", callback_data=f"update_{name_message}"))
        #     markup.add(types.InlineKeyboardButton("Ввести іншу назву", callback_data="new_name"))
        #     bot.send_message(
        #         message.chat.id,
        #         f"Подія з назвою '{name_message}' вже існує. Ви хочете оновити її або ввести іншу назву?",
        #         reply_markup=markup
        else:
            # Передаём название в process_name_step для обработки
            process_name_step(name_message)
    bot.register_next_step_handler(msg, name_or_cancel_step)

def process_name_step(message):
    # Сохраняем введённое имя/название в структуру user_data
    user_data["Ім'я/назва"] = {"title": [{"text": {"content": message.text}}]}
    # Переходим к следующему шагу — ввод даты
    msg = bot.send_message(message.chat.id, "Введіть дату у форматі DD-MM-YYYY:")
    bot.register_next_step_handler(msg, process_date_step)


def process_date_step(message):
    # Форматируем дату и добавляем время 08:00
    """
    Notion глючит из-за часового пояса. Время принимается в GMT 0,
    а по Киеву GMT+2. Выходит, что время ставиться на 2 часа раньше.
    Пускай программа работает только по Киеву.
    """
    try:
        date = datetime.strptime(message.text, '%d-%m-%Y')
        # date_needed = date.replace(hour=8, minute=0).astimezone(timezone.utc).isoformat()
        date_needed = get_kiev_time(date)
        user_data["Дата"] = {"date": {"start": date_needed, "end": None, "time_zone": "Europe/Kiev"}}
        msg = bot.send_message(message.chat.id, "Введіть текст привітання:")
        bot.register_next_step_handler(msg, process_greeting_text_step)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Некоректний формат дати! Спробуйте ще раз:")
        bot.register_next_step_handler(msg, process_date_step)


def process_greeting_text_step(message):
    # Сохраняем введённый текст привітання в структуру user_data
    user_data["Текст привітання"] = {"rich_text": [{"text": {"content": message.text}}]}
    # Передаём все собранные данные в функцию для создания страницы
    create_page(user_data)

    bot.send_message(message.chat.id, "Подію створено! Запис додано до бази даних Notion.")


# Установка на 8:00 по Киеву для process_date_step
def get_kiev_time(date):
    kiev_tz = pytz.timezone('Europe/Kiev')
    date = kiev_tz.localize(date.replace(hour=10, minute=0))  # устанавливаем 8:00 по киевскому времени
    return date.astimezone(pytz.utc).isoformat()  # переводим в UTC для хранения в Notion


# TODO Сделать логику для сохранения фото в папку, а потом выгрузки его в базу.


# ОБРОБКА ФУНКЦІЇ ПОКАЗАТИ ІМЕНА ПОДІЙ
@bot.message_handler(func=lambda message: message.text == "👥 Показати імена та назви свят")
def show_people(message):
    bot.send_message(message.chat.id, f"Імена та назви свят, наявні в базі:\n{show_people_names()}")
    bot.send_message(message.chat.id, "Бажаєте побачити весь текст подій, додати нову подію або оновити наявну?\n"
                                      "Ви можете зробити це за кнопками '📅 Показати події', '➕ Додати нову подію', "
                                      "'🔄 Оновити подію'.")


# ОБРОБКА ФУНКЦІЇ ПОКАЗАТИ ПОДІЇ
@bot.message_handler(func=lambda message: message.text == "🗒 Показати події")
def show_events(message):
    events = show_existing_events()
    if isinstance(events, str):  # Если вернулась ошибка
        bot.send_message(message.chat.id, events)
        return bot.send_message(message.chat.id, events)

    # Форматируем и выводим информацию о каждом событии
    output = []
    for details in events.values():
        event_info = (
            f"Ім'я/назва: {details['Ім\'я/назва']}\n"
            f"Дата: {details['Дата']}\n"
            f"Текст привітання: {details['Текст привітання']}\n"
        )
        output.append(event_info)

    # Объединяем всё в один текст и выводим
    final_output = "\n".join(output)
    bot.send_message(message.chat.id, f"Імена та назви подій, наявні в базі:\n\n{final_output}")


# ОБРОБКА ФУНКЦІЇ ВИДАЛИТИ ПОДІЮ
@bot.message_handler(func=lambda message: message.text == "❌ Видалити подію")
def delete_event_handler(message):
    msg = bot.send_message(message.chat.id, "Введіть ім'я/назву події для видалення або введіть 'відміна':")
    bot.register_next_step_handler(msg, handle_delete_name)


def handle_delete_name(name_message):
    name = name_message.text.strip()

    if name.lower() == "відміна":
        bot.send_message(name_message.chat.id, "Видалення скасовано.")
        start(name_message)  # Вернуть в главное меню, если нужно
        return

    # Ищем ID страницы по названию
    page_id = find_page_id_by_name(name)
    if page_id:
        delete_page(page_id, name_message)
        bot.send_message(name_message.chat.id, "Подію успішно видалено з бази!")
        start(name_message)
    else:
        bot.send_message(name_message.chat.id, "Подія з такою назвою не знайдена.")


#  ОБРОБКА ФУНКЦІЇ ОНОВИТИ ПОДІЮ
@bot.message_handler(func=lambda message: message.text == "🔄 Оновити подію")
def start_update_event(message):
    msg = bot.send_message(message.chat.id, "Введіть ім'я/назву події, яку хочете оновити, або введіть 'відміна':")
    bot.register_next_step_handler(msg, process_event_name_for_update)

bot_data = {}

def process_event_name_for_update(message):
    if message.text.lower() == "відміна":
        bot.send_message(message.chat.id, "Оновлення скасовано.")
        start(message)
        return

    event_name = message.text
    page_id = find_page_id_by_name(event_name)

    if not page_id:
        bot.send_message(message.chat.id, "Подію не знайдено. Перевірте назву та спробуйте ще раз.")
        return

    # Сохранение page_id для дальнейшего использования
    bot_data[message.chat.id] = {"page_id": page_id, "event_name": event_name}

    # Создание инлайн-кнопок для выбора обновления
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Оновити ім'я/назву", callback_data="update_name"),
        InlineKeyboardButton("Оновити текст", callback_data="update_text"),
        InlineKeyboardButton("Оновити дату події", callback_data="update_date")
    )
    bot.send_message(message.chat.id, "Оберіть, що саме ви хочете оновити:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("update_"))
def handle_update_selection(call):
    chat_id = call.message.chat.id
    action = call.data
    page_id = bot_data[chat_id]["page_id"]

    if action == "update_name":
        msg = bot.send_message(chat_id, "Введіть нове ім'я/назву:")
        bot.register_next_step_handler(msg, lambda m: update_single_field(m, page_id, "Ім'я/назва"))

    elif action == "update_text":
        msg = bot.send_message(chat_id, "Введіть новий текст події:")
        bot.register_next_step_handler(msg, lambda m: update_single_field(m, page_id, "Текст привітання"))

    elif action == "update_date":
        msg = bot.send_message(chat_id, "Введіть нову дату у форматі YYY-MM-DD:")
        bot.register_next_step_handler(msg, lambda m: update_single_field(m, page_id, "Дата"))


def update_single_field(message, page_id, field):
    new_value = message.text
    updated_data = {}

    if field == "Ім'я/назва":
        updated_data[field] = {"title": [{"text": {"content": new_value}}]}
    elif field == "Текст привітання":
        updated_data[field] = {"rich_text": [{"text": {"content": new_value}}]}
    elif field == "Дата":
        updated_data[field] = {"date": {"start": new_value}}

    result = update_page(page_id, updated_data)
    bot.send_message(message.chat.id, result)


@bot.message_handler(func=lambda message: message.text == "📅 Календар подій")
def handle_calendar_events(message):
    msg = bot.send_message(message.chat.id, "Введіть назви подій через кому, для яких потрібно запланувати нагадування/привітання.")
    bot.register_next_step_handler(msg, process_event_names, message.chat.id)

def process_event_names(message, chat_id):
    event_names = [name.strip() for name in message.text.split(",")]
    events_dict = show_existing_events()  # Получаем события из базы данных
    # Фильтруем события, чтобы оставить только те, что есть в БД
    selected_events = [event for event in events_dict.values() if event["Ім'я/назва"] in event_names]
    if not selected_events:
        bot.send_message(chat_id, "Жодної з введених подій не знайдено у базі даних.")
        return

    # Добавляем chat_id к каждому событию и передаем в поток для отправки поздравлений
    for event in selected_events:
        event["chat_id"] = chat_id

    setup_greeting_timers(selected_events)
    bot.send_message(chat_id, "Привітання/нагадування для вибраних подій будуть надіслані у визначений час.")

# Поток для отправки поздравлений
def send_greeting(event):
    """Отправка текста привітання и удаление события из БД."""
    chat_id = event.get('chat_id')
    greeting_text = event.get("Текст привітання")
    event_name = event.get("Ім'я/назва")
    event_time = event.get("Дата")

    # Отправляем поздравление
    bot.send_message(chat_id, f"{event_name}:\n{greeting_text}")

    # Удаляем событие из БД
    page_id = event.get("page_id")
    if page_id:
        delete_page(page_id, message=chat_id)  # передаем chat_id как параметр


def check_events(events):
    """Проверка списка событий и отправка поздравлений в указанное время."""
    while events:
        current_time = datetime.now().astimezone()  # Устанавливаем временную зону для текущего времени

        for event in events[:]:  # Используем копию списка для удаления
            event_time_str = event["Дата"]
            try:
                event_time = datetime.fromisoformat(event_time_str)  # Конвертируем в datetime с учетом временной зоны
            except ValueError:
                bot.send_message(events.chat.id, f"Ошибка: некорректный формат даты для события {event['Ім\'я/назва']}")
                continue

            # Логирование для отслеживания времени
            print(f"Текущее время: {current_time}, Время события: {event_time}")

            if event_time <= current_time:
                send_greeting(event)
                events.remove(event)  # Удаляем событие из списка для предотвращения повторной отправки
                print(f"Поздравление отправлено для события: {event['Ім\'я/назва']}")

        time.sleep(10)


def setup_greeting_timers(events):
    """Настройка и запуск потока для отправки поздравлений на указанные даты."""
    greeting_thread = threading.Thread(target=check_events, args=(events,))
    greeting_thread.daemon = True
    greeting_thread.start()


bot.polling()


