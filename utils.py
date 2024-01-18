from iqoption import connect_iq_option, purchase_with_gale
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def choose_candle_time(message, bot, user_purchase_params, user_credentials):
    print("Chegou na função 'choose_candle_time'")
    chat_id = message.chat.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('1 minuto'))
    markup.add(KeyboardButton('2 minutos'))
    markup.add(KeyboardButton('5 minutos'))
    markup.add(KeyboardButton('10 minutos'))

    bot.reply_to(message, "Por favor, escolha o tempo de expiração da vela:", reply_markup=markup)
    bot.register_next_step_handler(message, process_candle_time_step, bot, user_purchase_params, user_credentials)

def process_candle_time_step(message, bot, user_purchase_params, user_credentials):
    print("Chegou na função 'process_candle_time_step'")
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
    iq_api, _, success = connect_iq_option(email, password, account_type)

    # Verificar se a conexão foi bem-sucedida
    if iq_api:
        bot.reply_to(message, "Conectado com sucesso!")

        # Obter valores do user_purchase_params
        marker = user_purchase_params.get(chat_id, {}).get("marker")
        input_value = user_purchase_params.get(chat_id, {}).get("input_value")
        direction = user_purchase_params.get(chat_id, {}).get("direction")
        type = user_purchase_params.get(chat_id, {}).get("type")
        gale_quantity = user_purchase_params.get(chat_id, {}).get("gale_quantity")
        gale_multiplier = user_purchase_params.get(chat_id, {}).get("gale_multiplier")
        candle_time = user_purchase_params.get(chat_id, {}).get("candle_time")

        # Verificar se os valores necessários estão presentes
        if not all([marker, input_value, direction, type, gale_quantity, gale_multiplier]):
            bot.reply_to(message, "Parâmetros de compra incompletos. Use /purchase para começar uma nova compra.")
            return

        # Chamar a função de compra
        result = purchase_with_gale(iq_api, marker, input_value, direction, candle_time, type, gale_quantity, gale_multiplier)
        bot.send_message(chat_id, result["result"])
        # return jsonify(result)
        return result
    
    else:
        bot.reply_to(message, "Erro ao conectar. Verifique suas credenciais.")
