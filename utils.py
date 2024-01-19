from iqoption import connect_iq_option, purchase_with_gale
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def choose_candle_time(message, bot, user_purchase_params, user_credentials):
    # print("Arrived at the function 'choose_candle_time'")
    chat_id = message.chat.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('1 minute'))
    markup.add(KeyboardButton('2 minutes'))
    markup.add(KeyboardButton('5 minutes'))
    markup.add(KeyboardButton('10 minutos'))

    bot.reply_to(message, "Por favor, escolha o tempo de expiração da vela:", reply_markup=markup)
    bot.register_next_step_handler(message, process_candle_time_step, bot, user_purchase_params, user_credentials)

def process_candle_time_step(message, bot, user_purchase_params, user_credentials):
    # print("Arrived at the function 'process_candle_time_step'")
    chat_id = message.chat.id
    candle_time = message.text

    if candle_time == '1 minute':
        candle_time = 1
    elif candle_time == '2 minutes':
        candle_time = 2
    elif candle_time == '5 minutes':
        candle_time = 5
    elif candle_time == '10 minutes':
        candle_time = 10
    else:
        bot.reply_to(message, "Invalid choice. Use /expiration to try again.")
        return

    user_purchase_params[chat_id]["candle_time"] = candle_time

    email = user_credentials.get(chat_id, {}).get("email")
    password = user_credentials.get(chat_id, {}).get("password")
    account_type = user_credentials.get(chat_id, {}).get("account_type")

    if not email or not password or not account_type:
        bot.reply_to(message, "Please provide your credentials using the /connect command.")
        return

    iq_api, _, success = connect_iq_option(email, password, account_type)

    if iq_api:
        bot.reply_to(message, "Connected successfully!")

        marker = user_purchase_params.get(chat_id, {}).get("marker")
        input_value = user_purchase_params.get(chat_id, {}).get("input_value")
        direction = user_purchase_params.get(chat_id, {}).get("direction")
        type = user_purchase_params.get(chat_id, {}).get("type")
        gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
        gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")
        candle_time = user_purchase_params.get(chat_id, {}).get("candle_time")

        if not all([marker, input_value, direction, type, gale_quantity, gale_multiplier]):
            bot.reply_to(message, "Incomplete purchase parameters. Use /purchase to start a new purchase.")
            return

        result = purchase_with_gale(iq_api, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier, bot, chat_id)
        bot.send_message(chat_id, result["result"])
        return result
    
    else:
        bot.reply_to(message, "Error connecting. Check your credentials.")
