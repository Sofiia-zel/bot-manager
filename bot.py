import telebot
from telebot import types, TeleBot
from dotenv import load_dotenv
import os
from datetime import datetime, timezone, timedelta, tzinfo
from notion_integration import create_page, show_people_names, show_existing_events
import pytz


load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = TeleBot(TELEGRAM_TOKEN)

# Хранение данных о новом событии
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    add_event_btn = types.KeyboardButton("➕ Додати нову подію")
    show_events_btn = types.KeyboardButton("📅 Показати події")
    update_btn = types.KeyboardButton("🔄 Оновити подію")
    delete_btn = types.KeyboardButton("❌ Видалити подію")
    show_people_btn = types.KeyboardButton("👥 Показати імена та назви свят")
    keyboard.add(add_event_btn, show_events_btn, update_btn, delete_btn, show_people_btn)
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

    bot.send_message(message.chat.id, "Подію створено!")

# TODO Исправить ошибку с временем (или забить на нее)
# Установка на 8:00 по Киеву для process_date_step
def get_kiev_time(date):
    kiev_tz = pytz.timezone('Europe/Kiev')
    date = kiev_tz.localize(date.replace(hour=10, minute=0))  # устанавливаем 8:00 по киевскому времени
    return date.astimezone(pytz.utc).isoformat()  # переводим в UTC для хранения в Notion


# TODO Сделать логику для сохранения фото в папку, а потом выгрузки его в базу.


# ОБРОБКА ФУНКЦІЇ ПОКАЗАТИ ІМЕНА ПОДІЙ
@bot.message_handler(func=lambda message: message.text == "👥 Показати імена та назви свят")
def show_people(message):
    msg = bot.send_message(message.chat.id, f"Імена іменинників та назви свят, наявні в базі:\n{show_people_names()}")
    bot.send_message(message.chat.id, "Бажаєте побачити весь текст подій, додати нову подію або оновити наявну?\n"
                                      "Ви можете зробити це за кнопками '📅 Показати події', '➕ Додати нову подію', "
                                      "'🔄 Оновити подію'.")


# ОБРОБКА ФУНКЦІЇ ПОКАЗАТИ ПОДІЇ
@bot.message_handler(func=lambda message: message.text == "📅 Показати події")
def show_events(message):
    events = show_existing_events()
    if isinstance(events, str):  # Если вернулась ошибка
        bot.send_message(message.chat.id, events)
        return

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
    bot.send_message(message.chat.id, f"Імена іменинників та назви свят, наявні в базі:\n\n{final_output}")


bot.polling()


