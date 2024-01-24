from telebot import types
from state import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from ready_list import ready_lists

def handle_connect(bot):
    def command(message):
        chat_id = message.chat.id
        if chat_id in user_choices:
            bot.reply_to(message, "You have already provided your credentials previously. Use /email and /password to see.")
        else:
            bot.reply_to(message, "Please send your email.")
            from telegram_bot import process_email_step
            bot.register_next_step_handler(message, process_email_step)
    return command

def send_all_credentials(bot):
    def command(message):
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
    return command

def send_email_credentials(bot):
    def command(message):
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
    return command

def send_password_credentials(bot):
    def command(message):
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
    return command

def reset_credentials(bot):
    def command(message):
        chat_id = message.chat.id
        if chat_id in user_choices or chat_id in user_credentials or chat_id in user_purchase_params or chat_id in user_ready_lists:
            user_choices.pop(chat_id, None)
            user_credentials.pop(chat_id, None)
            user_purchase_params.pop(chat_id, None)
            user_ready_lists.pop(chat_id, None)
            bot.reply_to(message, "Account reset successfully.")
        else:
            bot.reply_to(message, "Nothing to be reset.")
    return command

def handle_disconnect(bot):
    def command(message):
        chat_id = message.chat.id

        if chat_id not in user_credentials:
            bot.reply_to(message, "You are not currently logged in. Use /connect to connect.")
            return

        user_credentials.pop(chat_id, None)
        user_choices.pop(chat_id, None)
        user_purchase_params.pop(chat_id, None)

        bot.reply_to(message, "Successfully disconnected.")
    return command

def handle_purchase(bot):
    def command(message):
        from telegram_bot import execute_purchase, process_marker_step
        chat_id = message.chat.id
        user_choices[chat_id]["stop_command_triggered"] = False

        if chat_id not in user_credentials:
            bot.reply_to(message, "You need to connect first. Use /connect to connect.")
            return

        if chat_id in user_purchase_params and user_purchase_params[chat_id]:
            bot.reply_to(message, "Starting purchase with predefined parameters.")
            execute_purchase(chat_id)
        else:
            bot.reply_to(message, "Please send the active for purchase.")
            bot.register_next_step_handler(message, process_marker_step)
    return command

def handle_reset_purchase(bot):
    def command(message):
        chat_id = message.chat.id

        if chat_id in user_purchase_params:
            del user_purchase_params[chat_id]
            bot.reply_to(message, "Purchase parameters reset successfully.")
        else:
            bot.reply_to(message, "You have not provided purchasing parameters. Use /purchase to start a new purchase.")
    return command

def handle_expiration(bot):
    def command(message):
        from utils import choose_candle_time
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
    return command

def send_welcome(bot):
    def command(message):
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
    return command

def handle_informations(bot):
    def command(message):
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
    return command

def handle_tutorial(bot):
    def command(message):
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
    return command

def handle_test_connection_status(bot):
    def command(message):
        chat_id = message.chat.id
        if chat_id in user_credentials:
            bot.send_message(chat_id, f"You are connected. Credentials: {user_credentials[chat_id]}")
        else:
            bot.send_message(chat_id, "You are not connected.")
    return command

def handle_show_ready_list(bot):
    def command(message):
        chat_id = message.chat.id
        if not ready_lists:
            bot.send_message(chat_id, "No ready lists are available at the moment.")
            return

        combined_ready_lists = {**ready_lists, **user_ready_lists.get(chat_id, {})}

        message_text = "📋 Ready Lists Available:\n\n"
        for list_name, list_details in combined_ready_lists.items():
            message_text += f"🔹 {list_name}:\n"
            for key, value in list_details.items():
                message_text += f"  - {key}: {value}\n"
            message_text += "\n"

        message_text += "Use the /use_ready_list command to use any of the ready lists above.\n\nOr if you prefer, you can create your own list with the /create_ready_list command."

        bot.send_message(chat_id, message_text)
    return command

def handle_use_ready_list(bot):
    def command(message):
        chat_id = message.chat.id

        if chat_id not in user_credentials:
            bot.reply_to(message, "You need to be logged in to use this feature. Please use /connect to log in.")
            return

        combined_ready_lists = {**ready_lists, **user_ready_lists.get(chat_id, {})}

        if not combined_ready_lists:
            bot.send_message(chat_id, "No ready lists are available. Use /create_ready_list to create one.")
            return

        markup = InlineKeyboardMarkup()
        for list_name in combined_ready_lists.keys():
            markup.add(InlineKeyboardButton(list_name, callback_data=f'list_{list_name}'))

        bot.send_message(chat_id, "Choose a ready list to use:", reply_markup=markup)
    return command

def handle_send_help(bot):
    def command(message):
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
    return command

def handle_send_all_commands(bot):
    def command(message):
        all_commands_message = """
📗 Command List 📗

Implemented Commands 🟢

Home and Help Commands:

/start - Starts the virtual assistant.
/commands - Lists all ChatBot commands.
/help - Provides a help guide.
/informations - Shows information about the ChatBot.
/tutorial - Shows information about the ChatBot.
/contact - Provides ways to contact those responsible for the bot.

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
/show_ready_list - Shows a ready-to-use list.
/use_read_list - Uses the ready list.
/create_ready_list - Creates a ready-to-use list.
"""
        bot.reply_to(message, all_commands_message)
    return command

def handle_start_create_ready_list(bot):
    def command(message):
        from telegram_bot import process_ready_list_name
        chat_id = message.chat.id
        msg = bot.send_message(chat_id, "Enter a name for your ready list:")
        bot.register_next_step_handler(msg, process_ready_list_name, chat_id)
    return command

def handle_get_last_purchase(bot):
    def command(message):
        chat_id = message.chat.id
        purchase_data = user_purchase_params.get(chat_id)

        if purchase_data:
            purchase_details = "\n".join([f"{key}: {value}" for key, value in purchase_data.items()])
            response_message = f"🛍️ Last Purchase Details:\n{purchase_details}"
        else:
            response_message = "No purchase data found."

        bot.reply_to(message, response_message)
    return command

def handle_stop(bot):
    def command(message):
        from telegram_bot import close_all_positions
        
        chat_id = message.chat.id
        user_data = user_credentials.get(chat_id)
        if not user_data or "iq_api_instance" not in user_data:
            bot.reply_to(message, "You are not connected. Please use /connect to connect.")
            return
        
        user_choices[chat_id]["stop_command_triggered"] = True
        API = user_data["iq_api_instance"]
        close_all_positions(API, bot, chat_id)
        bot.reply_to(message, "All operations have been halted.")

    return command
