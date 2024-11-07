
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