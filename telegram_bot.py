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
        bot.reply_to(message, "Você já forneceu suas credenciais anteriormente. Use /disconnect para se reconectar.")
    else:
        bot.reply_to(message, "Por favor, envie seu email.")
        bot.register_next_step_handler(message, process_email_step)

def process_email_step(message):
    chat_id = message.chat.id
    email = message.text
    user_choices[chat_id] = {"email": email}
    bot.reply_to(message, "Ótimo! Agora, por favor, envie sua senha.")
    bot.register_next_step_handler(message, process_password_step)

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text
    user_data = user_choices.get(chat_id)
    if user_data is None or "email" not in user_data:
        bot.reply_to(message, "Erro interno. Por favor, reinicie o processo.")
        return
    email = user_data["email"]
    user_choices[chat_id]["password"] = password
    iq_api, account_type, success = iqoption.connect_iq_option(email, password, 'demo')
    if success:
        user_choices[chat_id]["account_type"] = account_type
        user_credentials[chat_id] = {"email": email, "password": password, "account_type": account_type}
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('demo'), KeyboardButton('real'))
        bot.send_message(chat_id, "Conectado com sucesso! Escolha a conta para conectar:", reply_markup=markup)
        bot.register_next_step_handler(message, process_account_choice_step)
    else:
        bot.reply_to(message, "Falha na conexão. Verifique suas credenciais.")
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('/connect'))
        bot.send_message(chat_id, "Você deseja tentar conectar novamente?", reply_markup=markup)
        bot.register_next_step_handler(message, process_retry_connection_step)

def process_retry_connection_step(message):
    if message.text.lower() == '/connect':
        handle_connect_command(message)
    else:
        bot.reply_to(message, "Comando inválido. Use /connect para tentar novamente.")

def process_account_choice_step(message):
    chat_id = message.chat.id
    account_choice = message.text.lower()
    if account_choice not in ['demo', 'real']:
        bot.reply_to(message, "Escolha inválida. Use /connect para tentar novamente.")
        return
    user_choices[chat_id]["account_choice"] = account_choice
    iq_api, _, success = iqoption.connect_iq_option(user_choices[chat_id]["email"], user_choices[chat_id]["password"], user_choices[chat_id]["account_choice"])
    if success:
        bot.reply_to(message, f"Conectado com sucesso! Conta: {user_choices[chat_id]['account_choice']}")
        markup = ReplyKeyboardRemove()
        bot.send_message(chat_id, "Tipo de conta escolhido! Use /purchase para realizar operações.", reply_markup=markup)
    else:
        bot.reply_to(message, "Falha na conexão. Verifique suas credenciais.")

# Adicione aqui as demais funções para processar os comandos do bot (ex: handle_disconnect_command, handle_purchase_command, etc.)

@bot.message_handler(commands=['disconnect'])
def handle_disconnect_command(message):
    chat_id = message.chat.id

    # Remover as credenciais temporárias, se existirem
    if chat_id in user_credentials:
        # del user_credentials[chat_id]
        bot.reply_to(message, "Desconectado com sucesso.")
    else:
        bot.reply_to(message, "Você não está atualmente conectado. Use /connect para se conectar.")

@bot.message_handler(commands=['purchase'])
def handle_purchase_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário está conectado
    if chat_id not in user_credentials:
        print(f"DEBUG: Usuário {chat_id} não forneceu credenciais. Redirecionando para /connect.")
        bot.reply_to(message, "Você precisa se conectar primeiro. Use /connect para se conectar.")
        return

    # Verificar se o usuário já forneceu parâmetros de compra anteriormente
    if chat_id in user_purchase_params:
        print(f"DEBUG: Usuário {chat_id} já forneceu parâmetros de compra anteriormente.")
        bot.reply_to(message, "Você já forneceu os parâmetros de compra anteriormente. Use /reset_purchase para iniciar uma nova compra.")
    else:
        print(f"DEBUG: Solicitando ao usuário {chat_id} que envie o marcador (ativo) para a compra.")
        # Solicitar ao usuário que envie o marcador (ativo)
        bot.reply_to(message, "Por favor, envie o marcador (ativo) para a compra.")
        bot.register_next_step_handler(message, process_marker_step)

def process_marker_step(message):
    chat_id = message.chat.id
    marker = message.text

    # Armazenar temporariamente o marcador associado ao chat_id
    user_purchase_params[chat_id] = {"marker": marker}

    # Solicitar ao usuário que envie o valor de entrada
    bot.reply_to(message, "Ótimo! Agora, por favor, envie o valor de entrada.")
    bot.register_next_step_handler(message, process_input_value_step)

def process_input_value_step(message):
    chat_id = message.chat.id
    input_value = message.text

    # Verificar se o valor de entrada é um número válido
    try:
        input_value = float(input_value)
    except ValueError:
        bot.reply_to(message, "O valor de entrada deve ser um número válido.")
        return

    # Armazenar temporariamente o valor de entrada associado ao chat_id
    user_purchase_params[chat_id]["input_value"] = input_value

    # Solicitar ao usuário que envie a direção (call/put)
    bot.reply_to(message, "Ótimo! Agora, por favor, envie a direção da compra (call/put).")
    bot.register_next_step_handler(message, process_direction_step)

def process_direction_step(message):
    chat_id = message.chat.id
    direction = message.text.lower()

    # Verificar se a direção é válida
    if direction not in ['call', 'put']:
        bot.reply_to(message, "A direção da compra deve ser 'call' ou 'put'.")
        return

    # Armazenar temporariamente a direção associada ao chat_id
    user_purchase_params[chat_id]["direction"] = direction

    # Solicitar ao usuário que envie o tipo de compra (binary/digital)
    bot.reply_to(message, "Ótimo! Agora, por favor, envie o tipo de compra (binary/digital).")
    bot.register_next_step_handler(message, process_type_step)

def process_type_step(message):
    chat_id = message.chat.id
    type = message.text.lower()

    # Verificar se o tipo é válido
    if type not in ['binary', 'digital']:
        bot.reply_to(message, "O tipo de compra deve ser 'binary' ou 'digital'.")
        return

    # Armazenar temporariamente o tipo associado ao chat_id
    user_purchase_params[chat_id]["type"] = type

    # Solicitar ao usuário que envie a quantidade de operações Gale
    bot.reply_to(message, "Ótimo! Agora, por favor, envie a quantidade de operações Gale.")
    bot.register_next_step_handler(message, process_gale_quantity_step)

def process_gale_quantity_step(message):
    chat_id = message.chat.id
    gale_quantity = message.text

    # Verificar se a quantidade de operações Gale é um número inteiro válido
    try:
        gale_quantity = int(gale_quantity)
    except ValueError:
        bot.reply_to(message, "A quantidade de operações Gale deve ser um número inteiro válido.")
        return

    # Armazenar temporariamente a quantidade de operações Gale associada ao chat_id
    user_purchase_params[chat_id]["gale_quantity"] = gale_quantity

    # Solicitar ao usuário que envie o multiplicador de operações Gale
    bot.reply_to(message, "Ótimo! Agora, por favor, envie o multiplicador de operações Gale.")
    bot.register_next_step_handler(message, process_gale_multiplier_step)

def process_gale_multiplier_step(message):
    chat_id = message.chat.id
    gale_multiplier = message.text

    # Verificar se o multiplicador de operações Gale é um número válido
    try:
        gale_multiplier = float(gale_multiplier)
    except ValueError:
        bot.reply_to(message, "O multiplicador de operações Gale deve ser um número válido.")
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
        bot.reply_to(message, "Parâmetros de compra resetados com sucesso.")
    else:
        bot.reply_to(message, "Você não forneceu parâmetros de compra. Use /purchase para começar uma nova compra.")

# Função para lidar com o comando /choose_candle_time no Telegram
@bot.message_handler(commands=['choose_candle_time'])
def handle_choose_candle_time_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário já escolheu o tempo de expiração anteriormente
    if chat_id in user_choices:
        bot.reply_to(message, "Você já escolheu o tempo de expiração anteriormente. Use /reset_choice para fazer uma nova escolha.")
    else:
        # Criar botões de opção para o tempo de expiração da vela
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('1 minuto'))
        markup.add(KeyboardButton('2 minutos'))
        markup.add(KeyboardButton('5 minutos'))
        markup.add(KeyboardButton('10 minutos'))

        # Solicitar ao usuário que escolha o tempo de expiração da vela
        bot.reply_to(message, "Por favor, escolha o tempo de expiração da vela:", reply_markup=markup)
        bot.register_next_step_handler(message, process_candle_time_step)

def process_candle_time_step(message):
    chat_id = message.chat.id
    candle_time = message.text

    if candle_time == '1 minuto':
        candle_time = 1
    elif candle_time == '2 minutos':
        candle_time = 2
    elif candle_time == '5 minutos':
        candle_time = 5
    elif candle_time == '10 minutos':
        candle_time = 10
    else:
        bot.reply_to(message, "Escolha inválida. Use /expiration para tentar novamente.")
        return

    # user_purchase_params[chat_id]["duration"] = duration
    user_purchase_params[chat_id]["candle_time"] = candle_time

    # Verificar se as credenciais estão presentes
    email = user_credentials.get(chat_id, {}).get("email")
    password = user_credentials.get(chat_id, {}).get("password")
    account_type = user_credentials.get(chat_id, {}).get("account_type")

    if not email or not password or not account_type:
        bot.reply_to(message, "Por favor, forneça suas credenciais usando o comando /connect.")
        return

    # Chamar a função connect_iq_option para obter a API e o markup da próxima etapa
    iq_api, _, success = iqoption.connect_iq_option(email, password, account_type)

    # Verificar se a conexão foi bem-sucedida
    if iq_api:
        bot.reply_to(message, "Conectado com sucesso!")

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
            bot.send_message(chat_id, "Parâmetros de compra incompletos.")

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
        bot.reply_to(message, "Erro ao conectar. Verifique suas credenciais.")

# Função para lidar com o comando /reset_choice no Telegram
@bot.message_handler(commands=['reset_choice'])
def handle_reset_choice_command(message):
    chat_id = message.chat.id

    # Remover a escolha do usuário, se existir
    if chat_id in user_choices:
        # del user_choices[chat_id]
        bot.reply_to(message, "Escolha resetada com sucesso.")
    else:
        bot.reply_to(message, "Você ainda não fez uma escolha. Use /choose_candle_time para começar.")

@bot.message_handler(commands=['expiration'])
def handle_expiration_command(message):
    chat_id = message.chat.id

    # Verificar se o usuário está conectado
    if chat_id not in user_credentials:
        bot.reply_to(message, "Você precisa se conectar primeiro. Use /connect para se conectar.")
        return

    marker = user_purchase_params.get(chat_id, {}).get("marker")
    input_value = user_purchase_params.get(chat_id, {}).get("input_value")
    direction = user_purchase_params.get(chat_id, {}).get("direction")
    type = user_purchase_params.get(chat_id, {}).get("type")
    gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
    gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")

    if not all([marker, input_value, direction, type, gale_quantity, gale_multiplier]):
        bot.reply_to(message, "Parâmetros de compra incompletos. Use /purchase para começar uma nova compra.")
        return

    choose_candle_time(message, bot, user_purchase_params, user_credentials)

# Incluir a função send_welcome para os comandos /help e /start
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Oi! Eu sou o seu assistente para operações na IQ Option. 

Comandos disponíveis:
/connect - Conectar à IQ Option
/purchase - Realizar uma compra com estratégia Gale
/expiration - Escolher o tempo de expiração da vela
""")

# Função para lidar com todas as outras mensagens de texto
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "Desculpe, não entendi o que você quer. Use /help para ver os comandos disponíveis.")
