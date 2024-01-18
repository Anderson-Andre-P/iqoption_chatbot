import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import config
import iqoption
from utils import choose_candle_time

bot = telebot.TeleBot(config.API_TOKEN)

user_choices = {}
user_purchase_params = {}
user_credentials = {}

@bot.message_handler(commands=['connect'])
def handle_connect_command(message):
    chat_id = message.chat.id
    if chat_id in user_choices:
        bot.reply_to(message, "You have already provided your credentials previously. Use /disconnect to reconnect.")
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
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('demo'), KeyboardButton('real'))
        bot.send_message(chat_id, "Connected successfully! Choose the account to connect:", reply_markup=markup)
        bot.register_next_step_handler(message, process_account_choice_step)
    else:
        bot.reply_to(message, "Connection fail. Check your credentials.")
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('/connect'))
        bot.send_message(chat_id, "Do you want to try connecting again?", reply_markup=markup)
        bot.register_next_step_handler(message, process_retry_connection_step)

def process_retry_connection_step(message):
    if message.text.lower() == '/connect':
        handle_connect_command(message)
    else:
        bot.reply_to(message, "Invalid command. Use /connect to try again.")

def process_account_choice_step(message):
    chat_id = message.chat.id
    account_choice = message.text.lower()
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
        bot.reply_to(message, "Connection fail. Check your credentials.")

# Adicione aqui as demais funções para processar os comandos do bot (ex: handle_disconnect_command, handle_purchase_command, etc.)

@bot.message_handler(commands=['disconnect'])
def handle_disconnect_command(message):
    chat_id = message.chat.id

    # Remover as credenciais temporárias, se existirem
    if chat_id in user_credentials:
        # del user_credentials[chat_id]
        bot.reply_to(message, "Successfully disconnected.")
    else:
        bot.reply_to(message, "You are not currently logged in. Use /connect to connect.")

@bot.message_handler(commands=['purchase'])
def handle_purchase_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário está conectado
    if chat_id not in user_credentials:
        print(f"DEBUG: User {chat_id} did not provide credentials. Redirecting to /connect.")
        bot.reply_to(message, "You need to connect first. Use /connect to connect.")
        return

    # Verificar se o usuário já forneceu parâmetros de compra anteriormente
    if chat_id in user_purchase_params:
        print(f"DEBUG: User {chat_id} has already provided purchasing parameters previously.")
        bot.reply_to(message, "You have already provided the purchasing parameters previously. Use /reset_purchase to start a new purchase.")
    else:
        print(f"DEBUG: Prompting the user {chat_id} send the active for purchase.")
        # Solicitar ao usuário que envie o marcador (ativo)
        bot.reply_to(message, "Please send the active for purchase.")
        bot.register_next_step_handler(message, process_marker_step)

def process_marker_step(message):
    chat_id = message.chat.id
    marker = message.text

    # Armazenar temporariamente o marcador associado ao chat_id
    user_purchase_params[chat_id] = {"marker": marker}

    # Solicitar ao usuário que envie o valor de entrada
    bot.reply_to(message, "Excellent! Now please submit the down payment.")
    bot.register_next_step_handler(message, process_input_value_step)

def process_input_value_step(message):
    chat_id = message.chat.id
    input_value = message.text

    # Verificar se o valor de entrada é um número válido
    try:
        input_value = float(input_value)
    except ValueError:
        bot.reply_to(message, "The input value must be a valid number.")
        return

    # Armazenar temporariamente o valor de entrada associado ao chat_id
    user_purchase_params[chat_id]["input_value"] = input_value

    # Solicitar ao usuário que envie a direção (call/put)
    bot.reply_to(message, "Excellent! Now, please send the purchase direction (call/put).")
    bot.register_next_step_handler(message, process_direction_step)

def process_direction_step(message):
    chat_id = message.chat.id
    direction = message.text.lower()

    # Verificar se a direção é válida
    if direction not in ['call', 'put']:
        bot.reply_to(message, "The purchase direction must be 'call' or 'put'.")
        return

    # Armazenar temporariamente a direção associada ao chat_id
    user_purchase_params[chat_id]["direction"] = direction

    # Solicitar ao usuário que envie o tipo de compra (binary/digital)
    bot.reply_to(message, "Excellent! Now, please send the purchase type (binary/digital).")
    bot.register_next_step_handler(message, process_type_step)

def process_type_step(message):
    chat_id = message.chat.id
    type = message.text.lower()

    # Verificar se o tipo é válido
    if type not in ['binary', 'digital']:
        bot.reply_to(message, "The purchase type must be 'binary' or 'digital'.")
        return

    # Armazenar temporariamente o tipo associado ao chat_id
    user_purchase_params[chat_id]["type"] = type

    # Solicitar ao usuário que envie a quantidade de operações Gale
    bot.reply_to(message, "Excellent! Now please send the amount of Gale operations.")
    bot.register_next_step_handler(message, process_gale_quantity_step)

def process_gale_quantity_step(message):
    chat_id = message.chat.id
    gale_quantity = message.text

    # Verificar se a quantidade de operações Gale é um número inteiro válido
    try:
        gale_quantity = int(gale_quantity)
    except ValueError:
        bot.reply_to(message, "The number of Gale operations must be a valid integer.")
        return

    # Armazenar temporariamente a quantidade de operações Gale associada ao chat_id
    user_purchase_params[chat_id]["gale_quantity"] = gale_quantity

    # Solicitar ao usuário que envie o multiplicador de operações Gale
    bot.reply_to(message, "Excellent! Now please submit the Gale operations multiplier.")
    bot.register_next_step_handler(message, process_gale_multiplier_step)

def process_gale_multiplier_step(message):
    chat_id = message.chat.id
    gale_multiplier = message.text

    # Verificar se o multiplicador de operações Gale é um número válido
    try:
        gale_multiplier = float(gale_multiplier)
    except ValueError:
        bot.reply_to(message, "The Gale operations multiplier must be a valid number.")
        return

    # Armazenar temporariamente o multiplicador de operações Gale associado ao chat_id
    user_purchase_params[chat_id]["gale_multiplier"] = gale_multiplier

    choose_candle_time(message, bot, user_purchase_params, user_credentials)

# Função para lidar com o comando /reset_purchase no Telegram
@bot.message_handler(commands=['reset_purchase'])
def handle_reset_purchase_command(message):
    chat_id = message.chat.id

    # Remover os parâmetros temporários, se existirem
    if chat_id in user_purchase_params:
        # del user_purchase_params[chat_id]
        bot.reply_to(message, "Purchase parameters reset successfully.")
    else:
        bot.reply_to(message, "You have not provided purchasing parameters. Use /purchase to start a new purchase.")

# Função para lidar com o comando /choose_candle_time no Telegram
@bot.message_handler(commands=['choose_candle_time'])
def handle_choose_candle_time_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário já escolheu o tempo de expiração anteriormente
    if chat_id in user_choices:
        bot.reply_to(message, "You have already chosen the expiration time previously. Use /reset_choice to make a new choice.")
    else:
        # Criar botões de opção para o tempo de expiração da vela
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('1 minute'))
        markup.add(KeyboardButton('2 minutes'))
        markup.add(KeyboardButton('5 minutes'))
        markup.add(KeyboardButton('10 minutes'))

        # Solicitar ao usuário que escolha o tempo de expiração da vela
        bot.reply_to(message, "Please choose the candle expiration time:", reply_markup=markup)
        bot.register_next_step_handler(message, process_candle_time_step)

def process_candle_time_step(message):
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

    # user_purchase_params[chat_id]["duration"] = duration
    user_purchase_params[chat_id]["candle_time"] = candle_time

    # Verificar se as credenciais estão presentes
    email = user_credentials.get(chat_id, {}).get("email")
    password = user_credentials.get(chat_id, {}).get("password")
    account_type = user_credentials.get(chat_id, {}).get("account_type")

    if not email or not password or not account_type:
        bot.reply_to(message, "Please provide your credentials using the /connect command.")
        return

    # Chamar a função connect_iq_option para obter a API e o markup da próxima etapa
    iq_api, _, success = iqoption.connect_iq_option(email, password, account_type)

    # Verificar se a conexão foi bem-sucedida
    if iq_api:
        bot.reply_to(message, "Connected successfully!")

        # Obter valores do user_purchase_params
        purchase_params = user_purchase_params.get(chat_id, {})
        marker = user_purchase_params.get(chat_id, {}).get("marker")
        input_value = user_purchase_params.get(chat_id, {}).get("input_value")
        direction = user_purchase_params.get(chat_id, {}).get("direction")
        type = user_purchase_params.get(chat_id, {}).get("type")
        gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
        gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")
        candle_time = user_purchase_params.get(chat_id, {}).get("candle_time")

        if all([marker, input_value, direction, type, gale_quantity, gale_multiplier, candle_time]):
            result = iqoption.purchase_with_gale(iq_api, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier)
            bot.send_message(chat_id, result["result"])
        else:
            bot.send_message(chat_id, "Incomplete purchase parameters.")

        # # Verificar se os valores necessários estão presentes
        # if not all([marker, input_value, direction, type, gale_quantity, gale_multiplier]):
        #     bot.reply_to(message, "Parâmetros de compra incompletos. Use /purchase para começar uma nova compra.")
        #     return

        # Chamar a função de compra
        result = iqoption.purchase_with_gale(iq_api, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier)
        bot.send_message(chat_id, result["result"])
        # return jsonify(result)
        return result
    
    else:
        bot.reply_to(message, "Error connecting. Check your credentials.")

# Função para lidar com o comando /reset_choice no Telegram
@bot.message_handler(commands=['reset_choice'])
def handle_reset_choice_command(message):
    chat_id = message.chat.id

    # Remover a escolha do usuário, se existir
    if chat_id in user_choices:
        # del user_choices[chat_id]
        bot.reply_to(message, "Choice reset successfully.")
    else:
        bot.reply_to(message, "You haven't made a choice yet. Use /choose_candle_time to get started.")

@bot.message_handler(commands=['expiration'])
def handle_expiration_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário está conectado
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

# Incluir a função send_welcome para os comandos /help e /start
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hey! I am your assistant for operations at IQ Option. 

Available commands:
/connect - Connect to IQ Option
/purchase - Make a purchase with Gale strategy
/expiration - Choose the candle expiration time
""")

# Função para lidar com todas as outras mensagens de texto
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "Sorry, I don't understand what you want. Use /help to see available commands.")
