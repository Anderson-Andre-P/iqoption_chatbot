import telebot
import config
import iqoption
from utils import choose_candle_time

from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

bot = telebot.TeleBot(config.API_TOKEN)

user_choices = {}
user_purchase_params = {}
user_credentials = {}

@bot.message_handler(commands=['connect'])
def handle_connect_command(message):
    chat_id = message.chat.id
    if chat_id in user_choices:
        bot.reply_to(message, "You have already provided your credentials previously. Use /email and /password to see.")
    else:
        bot.reply_to(message, "Please send your email.")
        bot.register_next_step_handler(message, process_email_step)

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
        user_credentials[chat_id] = {"email": email, "password": password, "account_type": account_type}
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton('Demo', callback_data='demo'), InlineKeyboardButton('Real', callback_data='real'))
        bot.send_message(chat_id, "Connected successfully! Choose the account to connect:", reply_markup=markup)
    else:
        bot.reply_to(message, "The connection failed due to an internal problem or credentials sent with errors.\n\nCheck your credentials with the /email and /password commands.\n\nIf you believe this is a ChatBot issue, please contact us using the /contact.")

@bot.message_handler(commands=['credentials'])
def send_credentials(message):
    chat_id = message.chat.id
    user_data = user_choices.get(chat_id)

    if user_data is None:
        credentials_message = "No user data found."
    else:
        email = user_data.get("email")
        password = user_data.get("password")
        account_type = user_data.get("account_type")

        if email is not None and password is not None and account_type is not None:
            credentials_message = f"📧 Your email is: {email}\n🔒 Your password is: {password}\n💻 Your account type is: {account_type}."
        else:
            credentials_message = "Credentials not provided."

    bot.reply_to(message, credentials_message)


@bot.message_handler(commands=['email'])
def send_credentials(message):
    chat_id = message.chat.id
    user_data = user_choices.get(chat_id)
    if user_data is not None:
        email = user_data.get("email")
        if email is not None:
            email_message = f"📧 Your email is: {email}"
            bot.reply_to(message, email_message)
        else:
            bot.reply_to(message, "Email not provided.")
    else:
        bot.reply_to(message, "No user data found.")

@bot.message_handler(commands=['password'])
def send_credentials(message):
    chat_id = message.chat.id
    user_data = user_choices.get(chat_id)
    if user_data is not None:
        password = user_data.get("password")
        if password is not None:
            password_message = f"🔒 Your password is: {password}"
            bot.reply_to(message, password_message)
        else:
            bot.reply_to(message, "password not provided.")
    else:
        bot.reply_to(message, "No user data found.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    chat_id = call.message.chat.id
    choice = call.data

    if choice == "demo" or choice == "real":
        user_choices[chat_id]["account_choice"] = choice
        process_account_choice_step(call.message, call.data)
    elif choice == "call" or choice == "put":
        handle_direction_choice(call)
    elif choice == "binary" or choice == "digital":
        handle_purchase_type_choice(call)
    elif choice in ['1 minute', '5 minutes', '15 minutes']:
        handle_candle_time_choice(call)
    else:
        bot.reply_to(call.message, "Invalid choice. Use /connect to try again.")

def process_retry_connection_step(message):
    if message.text.lower() == '/connect':
        handle_connect_command(message)
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
        bot.send_message(chat_id, "Account type chosen! Use /purchase to perform operations.", reply_markup=markup)
    else:
        bot.reply_to(message, "Connection fail. Check your /email and /password.\nIf the email and password credentials are wrong, use the /reset command to provide new credentials.")

@bot.message_handler(commands=['reset'])
def reset_credentials(message):
    chat_id = message.chat.id
    if chat_id in user_choices:
        user_choices.pop(chat_id, None)
        user_credentials.pop(chat_id, None)
        user_purchase_params.pop(chat_id, None)
        bot.reply_to(message, "Account reset successfully.")
    else:
        bot.reply_to(message, "Nothing to be reset.")

@bot.message_handler(commands=['disconnect'])
def handle_disconnect_command(message):
    chat_id = message.chat.id

    if chat_id not in user_credentials:
        bot.reply_to(message, "You are not currently logged in. Use /connect to connect.")
        return

    user_credentials.pop(chat_id, None)
    user_choices.pop(chat_id, None)
    user_purchase_params.pop(chat_id, None)

    bot.reply_to(message, "Successfully disconnected.")

@bot.message_handler(commands=['purchase'])
def handle_purchase_command(message):
    chat_id = message.chat.id

    if chat_id not in user_credentials:
        bot.reply_to(message, "You need to connect first. Use /connect to connect.")
        return

    if chat_id in user_purchase_params:
        bot.reply_to(message, "You have already provided the purchasing parameters previously. Use /reset_purchase to start a new purchase.")
    else:
        bot.reply_to(message, "Please send the active for purchase.")
        bot.register_next_step_handler(message, process_marker_step)

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

            markup = InlineKeyboardMarkup(row_width=2)
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

    markup = InlineKeyboardMarkup(row_width=2)
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

@bot.message_handler(commands=['reset_purchase'])
def handle_reset_purchase_command(message):
    chat_id = message.chat.id

    if chat_id in user_purchase_params:
        del user_purchase_params[chat_id]
        bot.reply_to(message, "Purchase parameters reset successfully.")
    else:
        bot.reply_to(message, "You have not provided purchasing parameters. Use /purchase to start a new purchase.")

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

@bot.message_handler(commands=['choose_candle_time'])
def handle_expiration_command(message):
    chat_id = message.chat.id

    if chat_id not in user_credentials:
        bot.reply_to(message, "You need to connect first. Use /connect to connect.")
        return

    marker = user_purchase_params.get(chat_id, {}).get("marker")
    input_value = user_purchase_params.get(chat_id, {}).get("input_value")
    direction = user_purchase_params.get(chat_id, {}).get("direction")
    type = user_purchase_params.get(chat_id, {}).get("type")
    gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
    gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")

    if not all([marker, input_value, direction, type, gale_quantity, gale_multiplier]):
        bot.reply_to(message, "Incomplete purchase parameters. Use /purchase to start a new purchase.")
        return

    choose_candle_time(message, bot, user_purchase_params, user_credentials)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    start_message =  """
🤖 Hello! I'm your operations assistant at IQ Option.

To start operations via IQ Option you need to type the /connect command and provide your access data to log in.

Or if you prefer, you can use the commands below:

/help to ask for help
/commands to get a list of commands available in this chat
/informations to access relevant Bot information
/tutorial to access a quick tutorial.
"""
    bot.reply_to(message, start_message)
    
@bot.message_handler(commands=['help'])
def send_help(message):
    help_message = """
🤖 How can I help you today?

Here are some useful commands you can use:

/help - Displays this help message.
/start - Starts the conversation with the bot.
/commands - Shows a list of available commands.
/informations - Provides information about the bot.
/tutorial - Provides information about the bot.

If you have any questions or need additional assistance, please feel free to ask. I am here to help!
"""
    bot.reply_to(message, help_message)

@bot.message_handler(commands=['commands'])
def send_all_commands(message):
    all_commands_message = """
📗 Command List 📗

Implemented Commands 🟢

Home and Help Commands:

/start - Starts the virtual assistant.
/commands - Lists all ChatBot commands.
/help - Provides a help guide.
/informations - Shows information about the ChatBot.
/tutorial - Shows information about the ChatBot.
/stop - Stops the bot from functioning.

Connection Commands with IQ Option:

/connect - Starts the connection with the IQ Option platform.
/disconnect - Terminates the connection with the IQ Option platform.

Commands with User Data:

/credentials - Shows the provided email and password credentials.
/email - Shows the provided email.
/password - Shows the provided password.
/reset - Deletes all settings for the account present in that chat

Trading Commands:

/purchase - Starts the process of purchasing an asset.
/reset_purchase - Reset purchase information for the last asset.
/choose_candle_time - Allows you to choose the candle expiration time (1, 5 or 15 minutes).
"""
# Unimplemented Commands 🔴

# User Data Management:

# /clear_user_data - Clears user data.
# /get_last_purchase - Shows the last purchase operation performed.
# /create_ready_list - Creates a ready-to-use list.
# /show_ready_list - Shows a ready-to-use list.
# /use_read_list - Uses the ready list.
# /connect_order_blocks - Connects to Order Blocks.
# /configurations - Shows the settings used in the ChatBot.
# /adjusts_menu - Allows you to modify ChatBot settings.
    bot.reply_to(message, all_commands_message)

@bot.message_handler(commands=['informations'])
def send_all_commands(message):
    informations = """
📉 Informations of this Bot 📈

This bot was developed to assist in the process of purchasing assets on the IQ Option platform.

Our objective with the Bot is to provide trading assistance to improve and increase your results.

With it you can connect faster and more simply on the platform.

It doesn't stop there, the Bot is still capable of helping you make smarter purchases and consequently you end up being able to manage your time better.

Additionally, this bot is available to answer questions, provide useful information and guidance whenever you need it.

Please remember that this wizard is designed to help you, but it is important to trade responsibly and understand the risks involved in the financial market. Feel free to explore the available features and commands. I'm here to make your IQ Option experience more efficient and effective.
"""
    bot.reply_to(message, informations)

@bot.message_handler(commands=['tutorial'])
def send_all_commands(message):
    informations = """
Tutorial

Welcome to the tutorial for using this bot on the IQ Option platform! We are here to make your trading experience easier. Here are some starting tips:

1. Useful Commands:
    - If you need help or want to see a list of available commands, type /help at any time.
    - For additional information about the bot, including its purpose and features, type /informations.

2. Connection to IQ Option:
    - Use the /connect command to quickly connect to your IQ Option account directly from this chat.

3. Making Purchases:
    - When you are ready to make a purchase of financial assets, use the /purchase command. The bot will follow the Gale strategy to help with your operations.

4. Time Management:
    - Customize the candle expiration time for your trades with the /choose_candle_time command. This allows you to tailor your trades to your preferences.

5. Assistance and Support:
    - This bot is here to provide support and assistance during your trades on IQ Option. Don't hesitate to ask questions or request guidance.

Remember that you are in control of your trading, and this bot is here to make the process more efficient and informative. Trade responsibly and take advantage of the features offered. We are here to help and make your trading experience smoother.
"""
    bot.reply_to(message, informations)

@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "Sorry, I don't understand what you want. Use /help to see available commands.")
