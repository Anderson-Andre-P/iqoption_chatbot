import telebot
import config
import iqoption
from utils import choose_candle_time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from handlers.handlers import handle_connect, handle_expiration, handle_informations, handle_reset_purchase, handle_send_all_commands, handle_send_help, handle_show_ready_list, handle_start_create_ready_list, handle_test_connection_status, handle_tutorial, handle_use_ready_list, send_all_credentials, send_email_credentials, send_password_credentials, handle_purchase, handle_disconnect, reset_credentials, send_welcome
from state import user_choices, user_purchase_params, user_credentials, user_ready_lists
from ready_list import ready_lists
 
bot = telebot.TeleBot(config.API_TOKEN)

def register_handlers():
    bot.message_handler(commands=['connect'])(handle_connect(bot))
    bot.message_handler(commands=['credentials'])(send_all_credentials(bot))
    bot.message_handler(commands=['email'])(send_email_credentials(bot))
    bot.message_handler(commands=['password'])(send_password_credentials(bot))
    bot.message_handler(commands=['purchase'])(handle_purchase(bot))
    bot.message_handler(commands=['disconnect'])(handle_disconnect(bot))
    bot.message_handler(commands=['reset'])(reset_credentials(bot))
    bot.message_handler(commands=['show_ready_list'])(handle_show_ready_list(bot))
    bot.message_handler(commands=['start'])(send_welcome(bot))
    bot.message_handler(commands=['tutorial'])(handle_tutorial(bot))
    bot.message_handler(commands=['informations'])(handle_informations(bot))
    bot.message_handler(commands=['help'])(handle_send_help(bot))
    bot.message_handler(commands=['commands'])(handle_send_all_commands(bot))
    bot.message_handler(commands=['test_conection'])(handle_test_connection_status(bot))
    bot.message_handler(commands=['use_ready_list'])(handle_use_ready_list(bot))
    bot.message_handler(commands=['reset_purchase'])(handle_reset_purchase(bot))
    bot.message_handler(commands=['choose_candle_time'])(handle_expiration(bot))
    bot.message_handler(commands=['create_ready_list'])(handle_start_create_ready_list(bot))

register_handlers()

def process_email_step(message):
    chat_id = message.chat.id
    email = message.text
    user_choices[chat_id] = {"email": email}
    bot.reply_to(message, "Excellent! Now please submit your password.")
    bot.register_next_step_handler(message, process_password_step)

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text
    user_data = user_choices.get(chat_id)
    if user_data is None or "email" not in user_data:
        bot.reply_to(message, "Internal error. Please restart the process.")
        return
    email = user_data["email"]
    user_choices[chat_id]["password"] = password
    iq_api, account_type, success = iqoption.connect_iq_option(email, password, 'demo')
    if success:
        user_choices[chat_id]["account_type"] = account_type
        user_credentials[chat_id] = {
            "email": email,
            "password": password,
            "account_type": account_type,
            "iq_api_instance": iq_api
        }
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Demo', callback_data='demo'), InlineKeyboardButton('Real', callback_data='real'))
        bot.send_message(chat_id, "Connected successfully! Choose the account to connect:", reply_markup=markup)
    else:
        bot.reply_to(message, "The connection failed due to an internal problem or credentials sent with errors.\n\nCheck your credentials with the /email and /password commands.\n\nIf you believe this is a ChatBot issue, please contact us using the /contact.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    choice = call.data

    if choice.startswith('list_'):
        list_name = choice.split('_', 1)[1]
        combined_ready_lists = {**ready_lists, **user_ready_lists.get(chat_id, {})}
        chosen_list = combined_ready_lists.get(list_name)
        if chosen_list:
            user_purchase_params[chat_id] = chosen_list
            bot.answer_callback_query(call.id, f"You have chosen: {list_name}")
            bot.send_message(chat_id, f"List '{list_name}' selected. Use /purchase to start purchasing with these parameters.")
        else:
            bot.answer_callback_query(call.id, "Invalid choice.")
            bot.send_message(chat_id, "An error occurred. Please try again.")
    elif choice.startswith('direction_'):
        process_direction(call)
    elif choice.startswith('type_'):
        process_type(call)
    elif choice.startswith('candle_time_'):
        process_candle_time(call)

    elif choice in ['demo', 'real']:
        user_choices[chat_id]["account_choice"] = choice
        process_account_choice_step(call.message, choice)

    elif choice in ['call', 'put']:
        handle_direction_choice(call)

    elif choice in ['binary', 'digital']:
        handle_purchase_type_choice(call)

    elif choice in ['1 minute', '5 minutes', '15 minutes']:
        handle_candle_time_choice(call)

    else:
        bot.answer_callback_query(call.id, "Invalid choice.")

def process_retry_connection_step(message):
    if message.text.lower() == '/connect':
        handle_connect(message)
    else:
        bot.reply_to(message, "Invalid command. Use /connect to try again.")

def process_account_choice_step(message, choice):
    chat_id = message.chat.id
    account_choice = choice

    if account_choice not in ['demo', 'real']:
        bot.reply_to(message, "Invalid choice. Use /connect to try again.")
        return
    
    user_choices[chat_id]["account_choice"] = account_choice
    iq_api, _, success = iqoption.connect_iq_option(user_choices[chat_id]["email"], user_choices[chat_id]["password"], user_choices[chat_id]["account_choice"])

    if success:
        bot.reply_to(message, f"Connected successfully! Account: {user_choices[chat_id]['account_choice']}")
        markup = ReplyKeyboardRemove()
        bot.send_message(chat_id, "Account type chosen!\n\nUse /purchase to perform operations or /show_ready_list to see pre-configured operations.", reply_markup=markup)
    else:
        bot.reply_to(message, "Connection fail. Check your /email and /password.\nIf the email and password credentials are wrong, use the /reset command to provide new credentials.")

def execute_purchase(chat_id):
    purchase_params = user_purchase_params.get(chat_id, {})
    
    required_params = ["marker", "input_value", "direction", "type", "gale_quantity", "gale_multiplier", "candle_time"]
    if not all(param in purchase_params for param in required_params):
        bot.send_message(chat_id, "Incomplete purchase parameters. Please use /use_ready_list or set parameters manually.")
        return

    try:
        marker = purchase_params["marker"]
        input_value = float(purchase_params["input_value"])
        direction = purchase_params["direction"]
        type = purchase_params["type"]
        gale_quantity = int(purchase_params["gale_quantity"])
        gale_multiplier = float(purchase_params["gale_multiplier"])
        candle_time = int(purchase_params["candle_time"])
    except ValueError as e:
        bot.send_message(chat_id, f"Error in purchase parameters: {e}")
        return

    user_data = user_credentials.get(chat_id)
    if not user_data:
        bot.send_message(chat_id, "You are not connected. Please use /connect to connect.")
        return

    user_data = user_credentials.get(chat_id)
    API = user_data.get("iq_api_instance") if user_data else None
    if not API:
        bot.send_message(chat_id, "API connection is not established. Please reconnect.")
        return

    result = iqoption.purchase_with_gale(API, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier, bot, chat_id)
    
    bot.send_message(chat_id, result["result"])

def process_marker_step(message):
    chat_id = message.chat.id
    marker = message.text

    user_purchase_params[chat_id] = {"marker": marker}

    bot.reply_to(message, "Excellent! Now please submit the down payment.")
    bot.register_next_step_handler(message, process_input_value_response)

def process_input_value_response(message):
    chat_id = message.chat.id
    input_value = message.text

    try:
        input_value = float(input_value)
        if isinstance(input_value, float):
            user_purchase_params[chat_id]["input_value"] = input_value

            markup = InlineKeyboardMarkup()
            call_button = InlineKeyboardButton("Call", callback_data="call")
            put_button = InlineKeyboardButton("Put", callback_data="put")
            markup.add(call_button, put_button)

            bot.send_message(chat_id, "Please choose the purchase direction:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "The input value must be a valid float number. Please try again.")
            bot.register_next_step_handler(message, process_input_value_response)
    except ValueError:
        bot.send_message(chat_id, "The input value must be a valid number. Please try again.")
        bot.register_next_step_handler(message, process_input_value_response)

@bot.callback_query_handler(func=lambda call: call.data in ["call", "put"])
def handle_direction_choice(call):
    chat_id = call.message.chat.id
    direction = call.data
    user_purchase_params[chat_id]["direction"] = direction

    bot.answer_callback_query(call.id, f"You have chosen: {direction.capitalize()}")

    bot.send_message(chat_id, f"You have chosen: {direction.capitalize()}")

    markup = InlineKeyboardMarkup()
    binary_button = InlineKeyboardButton("Binary", callback_data="binary")
    digital_button = InlineKeyboardButton("Digital", callback_data="digital")
    markup.add(binary_button, digital_button)

    bot.send_message(chat_id, "Please choose the purchase type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["binary", "digital"])
def handle_purchase_type_choice(call):
    chat_id = call.message.chat.id
    purchase_type = call.data
    user_purchase_params[chat_id]["type"] = purchase_type

    bot.answer_callback_query(call.id, f"You have chosen: {purchase_type.capitalize()}")
    bot.send_message(chat_id, f"You have chosen: {purchase_type.capitalize()}")

    bot.send_message(chat_id, "Please send the number of Gale operations.")
    bot.register_next_step_handler_by_chat_id(chat_id, process_gale_quantity_step)

def process_type_step(message):
    chat_id = message.chat.id
    type_choice = message.text.lower()

    print(f'Type Choice {type_choice}\n\n\n')
    print(f'Message {message}\n\n\n')

    if type_choice not in ['binary', 'digital']:
        bot.reply_to(message, "The purchase type must be 'binary' or 'digital'.")
        return

    user_purchase_params[chat_id]["type"] = type_choice

    bot.reply_to(message, "Excellent! Now please send the amount of Gale operations.")
    bot.register_next_step_handler(message, process_gale_quantity_step)

def process_gale_quantity_step(message):
    chat_id = message.chat.id
    gale_quantity = message.text

    try:
        gale_quantity = int(gale_quantity)
    except ValueError:
        bot.reply_to(message, "The number of Gale operations must be a valid integer.")
        return

    user_purchase_params[chat_id]["gale_quantity"] = gale_quantity

    bot.reply_to(message, "Excellent! Now please submit the Gale operations multiplier.")
    bot.register_next_step_handler(message, process_gale_multiplier_step)

def process_gale_multiplier_step(message):
    chat_id = message.chat.id
    gale_multiplier = message.text

    try:
        gale_multiplier = float(gale_multiplier)
    except ValueError:
        bot.reply_to(message, "The Gale operations multiplier must be a valid number.")
        return

    user_purchase_params[chat_id]["gale_multiplier"] = gale_multiplier

    choose_candle_time(message, bot, user_purchase_params, user_credentials)

@bot.callback_query_handler(func=lambda call: call.data in ['1 minute', '2 minutes', '5 minutes', '10 minutes'])
def handle_candle_time_choice(call):
    chat_id = call.message.chat.id
    candle_time = call.data

    print(f'chat id: {chat_id}\n\n')
    print(f'cancle time: {candle_time}\n\n')

    if candle_time == '1 minute':
        candle_time_value = 1
    elif candle_time == '5 minutes':
        candle_time_value = 5
    elif candle_time == '15 minutes':
        candle_time_value = 15
    else:
        bot.answer_callback_query(call.id, "Invalid choice.")
        return

    user_purchase_params[chat_id]["candle_time"] = candle_time_value
    bot.answer_callback_query(call.id, f"Candle time chosen: {candle_time}")
    bot.send_message(chat_id, f"You have chosen a candle expiration time of {candle_time}.")

    email = user_credentials.get(chat_id, {}).get("email")
    password = user_credentials.get(chat_id, {}).get("password")
    account_type = user_credentials.get(chat_id, {}).get("account_type")

    if not email or not password or not account_type:
        bot.reply_to(call.message, "Please provide your credentials using the /connect command.")
        return

    iq_api, _, success = iqoption.connect_iq_option(email, password, account_type)

    if iq_api:
        bot.reply_to(call.message, "Operation started.")
        bot.reply_to(call.message, "Waiting for the operation to complete...")

        purchase_params = user_purchase_params.get(chat_id, {})
        marker = user_purchase_params.get(chat_id, {}).get("marker")
        input_value = user_purchase_params.get(chat_id, {}).get("input_value")
        direction = user_purchase_params.get(chat_id, {}).get("direction")
        type = user_purchase_params.get(chat_id, {}).get("type")
        gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
        gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")
        candle_time = user_purchase_params.get(chat_id, {}).get("candle_time")

        if all([marker, input_value, direction, type, gale_quantity, gale_multiplier, candle_time]):
            result = iqoption.purchase_with_gale(iq_api, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier, bot, chat_id)
            bot.send_message(chat_id, result["result"])
        else:
            bot.send_message(chat_id, "Incomplete purchase parameters.")

        return result
    
    else:
        bot.reply_to(call.message, "Error connecting. Check your credentials.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
def handle_list_choice(call):
    chat_id = call.message.chat.id
    list_name = call.data.split('_', 1)[1]
    combined_ready_lists = {**ready_lists, **user_ready_lists.get(chat_id, {})}
    chosen_list = combined_ready_lists.get(list_name)
    if chosen_list:
        user_purchase_params[chat_id] = chosen_list
        bot.answer_callback_query(call.id, f"You have chosen: {list_name}")
        bot.send_message(chat_id, f"List '{list_name}' selected. Use /purchase to start purchasing with these parameters.")
    else:
        bot.answer_callback_query(call.id, "Invalid choice.")
        bot.send_message(chat_id, "An error occurred. Please try again.")

def process_ready_list_name(message, chat_id):
    list_name = message.text
    user_ready_lists[chat_id] = {list_name: {}}
    
    msg = bot.send_message(chat_id, "Enter the marker (e.g., EURUSD):")
    bot.register_next_step_handler(msg, process_marker, chat_id, list_name)

def process_marker(message, chat_id, list_name):
    marker = message.text
    user_ready_lists[chat_id][list_name]["marker"] = marker
    
    msg = bot.send_message(chat_id, "Enter the input value:")
    bot.register_next_step_handler(msg, process_input_value, chat_id, list_name)

def process_input_value(message, chat_id, list_name):
    input_value = message.text
    user_ready_lists[chat_id][list_name]["input_value"] = input_value

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Call", callback_data=f"direction_call_{list_name}"),
               InlineKeyboardButton("Put", callback_data=f"direction_put_{list_name}"))
    bot.send_message(chat_id, "Choose the direction:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('direction_'))
def process_direction(call):
    chat_id = call.message.chat.id
    _, direction, list_name = call.data.split('_')
    user_ready_lists[chat_id][list_name]["direction"] = direction

    user_ready_lists[chat_id][list_name]["direction"] = direction

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Binary", callback_data=f"type_binary_{list_name}"),
               InlineKeyboardButton("Digital", callback_data=f"type_digital_{list_name}"))
    bot.send_message(chat_id, "Choose the type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def process_type(call):
    chat_id = call.message.chat.id
    _, type, list_name = call.data.split('_')
    user_ready_lists[chat_id][list_name]["type"] = type

    user_ready_lists[chat_id][list_name]["type"] = type

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("1 minute", callback_data=f"candle_time_1_{list_name}"),
               InlineKeyboardButton("5 minutes", callback_data=f"candle_time_5_{list_name}"),
               InlineKeyboardButton("15 minutes", callback_data=f"candle_time_15_{list_name}"))
    bot.send_message(chat_id, "Choose the candle time:", reply_markup=markup)

def process_gale_quantity(message, chat_id, list_name):
    gale_quantity = message.text
    user_ready_lists[chat_id][list_name]["gale_quantity"] = gale_quantity

    msg = bot.send_message(chat_id, "Enter the Gale multiplier:")
    bot.register_next_step_handler(msg, process_gale_multiplier, chat_id, list_name)

def process_gale_multiplier(message, chat_id, list_name):
    gale_multiplier = message.text
    user_ready_lists[chat_id][list_name]["gale_multiplier"] = gale_multiplier

    msg = bot.send_message(chat_id, "Enter the candle time (1, 5 or 15):")
    bot.register_next_step_handler(msg, process_candle_time, chat_id, list_name)

def ask_gale_quantity(message, chat_id, list_name):
    msg = bot.send_message(chat_id, "Enter the number of Gale operations:")
    bot.register_next_step_handler(msg, process_gale_quantity, chat_id, list_name)

def process_gale_quantity(message, chat_id, list_name):
    gale_quantity = message.text
    try:
        gale_quantity = int(gale_quantity)
        user_ready_lists[chat_id][list_name]["gale_quantity"] = gale_quantity
        ask_gale_multiplier(message, chat_id, list_name)
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid integer for Gale operations.")
        ask_gale_quantity(message, chat_id, list_name)

def ask_gale_multiplier(message, chat_id, list_name):
    msg = bot.send_message(chat_id, "Enter the Gale multiplier:")
    bot.register_next_step_handler(msg, process_gale_multiplier, chat_id, list_name)

def process_gale_multiplier(message, chat_id, list_name):
    gale_multiplier = message.text
    try:
        gale_multiplier = float(gale_multiplier)
        user_ready_lists[chat_id][list_name]["gale_multiplier"] = gale_multiplier
        bot.send_message(chat_id, f"Custom list '{list_name}' added successfully.")
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid number for the Gale multiplier.")
        ask_gale_multiplier(message, chat_id, list_name)

@bot.callback_query_handler(func=lambda call: call.data.startswith('candle_time_'))
def process_candle_time(call):
    chat_id = call.message.chat.id
    data_parts = call.data.split('_')
    candle_time_str = data_parts[2]
    list_name = '_'.join(data_parts[3:])

    try:
        candle_time = int(candle_time_str)
        user_ready_lists[chat_id][list_name]["candle_time"] = candle_time
        ask_gale_quantity(call.message, chat_id, list_name)
    except ValueError:
        bot.send_message(chat_id, "Invalid candle time. Please enter a number.")

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "Sorry, I don't understand what you want. Use /help to see available commands.")
