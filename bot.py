import requests
import telebot
from telebot import types, TeleBot
from dotenv import load_dotenv
import os
from notion_integration import create_page


# from app.add_new_event.new_event import process_name_step, process_date_step, process_greeting_text_step



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
    msg = bot.send_message(message.chat.id, "Введіть ім'я або назву події:")
    bot.register_next_step_handler(msg, process_name_step)


def process_name_step(message):
    # Сохраняем введённое имя/название в структуру user_data
    user_data["Ім'я/назва"] = {"title": [{"text": {"content": message.text}}]}
    msg = bot.send_message(message.chat.id, "Введіть дату у форматі YYYY-MM-DD:")
    bot.register_next_step_handler(msg, process_date_step)


def process_date_step(message):
    # Сохраняем введённую дату в структуру user_data
    user_data["Дата"] = {"date": {"start": message.text, "end": None}}
    msg = bot.send_message(message.chat.id, "Введіть текст привітання:")
    bot.register_next_step_handler(msg, process_greeting_text_step)


def process_greeting_text_step(message):
    # Сохраняем введённый текст привітання в структуру user_data
    user_data["Текст привітання"] = {"rich_text": [{"text": {"content": message.text}}]}
    # Вызываем функцию для добавления записи в Notion
    bot.send_message(message.chat.id, "Подію створено!")


    # TODO Сделать логику для сохранения фото в папку, а потом выгрузки его в базу.
    # elif step == "photo":
    #     if message.content_type == "photo":
    #         # Сохранение фото и завершение ввода данных
    #         user_data[user_id]["photo"] = message.photo[-1].file_id  # Использование самого высокого качества фото
    #         bot.send_message(message.chat.id, "Подія успішно збережена!")
    #
    #         # Сохранение данных в БД или другой системе хранения
    #         # save_event_to_db(user_data[user_id])  # функция для сохранения
    #
    #         # Очистка данных пользователя из user_data
    #         # del user_data[user_id]
    #     else:
    #         bot.send_message(message.chat.id, "Будь ласка, надішліть фото, а не текст.")


    print(user_data)




# @bot.message_handler(commands=['add_new_event'])
# def start_add_event(message):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     markup.add(types.KeyboardButton("Отмена"))
#     bot.send_message(
#         message.chat.id,
#         "Введите название события или нажмите 'Отмена' для выхода:",
#         reply_markup=markup
#     )
#     bot.register_next_step_handler(message, get_title)
#
#
# def get_title(message):
#     if message.text.lower() == "отмена":
#         bot.send_message(message.chat.id, "Добавление события отменено.", reply_markup=types.ReplyKeyboardRemove())
#         return
#
#     user_data['title'] = message.text
#     bot.send_message(message.chat.id, "Введите дату события (в формате ГГГГ-ММ-ДД):")
#     bot.register_next_step_handler(message, get_date)
#
#
# def get_date(message):
#     if message.text.lower() == "отмена":
#         bot.send_message(message.chat.id, "Добавление события отменено.", reply_markup=types.ReplyKeyboardRemove())
#         return
#
#     user_data['date'] = message.text
#     bot.send_message(message.chat.id, "Введите описание события:")
#     bot.register_next_step_handler(message, get_description)
#
#
# def get_description(message):
#     if message.text.lower() == "отмена":
#         bot.send_message(message.chat.id, "Добавление события отменено.", reply_markup=types.ReplyKeyboardRemove())
#         return
#
#     user_data['description'] = message.text
#
#     # Отправка данных в Notion
#     title = user_data.get('title')
#     date = user_data.get('date')
#     description = user_data.get('description')
#
#     success = add_event_to_notion(title, date, description)
#
#     if success:
#         bot.send_message(message.chat.id, "Событие успешно добавлено в базу данных Notion!",
#                          reply_markup=types.ReplyKeyboardRemove())
#     else:
#         bot.send_message(message.chat.id, "Произошла ошибка при добавлении события.",
#                          reply_markup=types.ReplyKeyboardRemove())


bot.polling()


