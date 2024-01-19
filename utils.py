from iqoption import connect_iq_option, purchase_with_gale
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

def choose_candle_time(message, bot, user_purchase_params, user_credentials):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton('1 minute', callback_data='1 minute'))
    markup.add(InlineKeyboardButton('5 minutes', callback_data='5 minutes'))
    markup.add(InlineKeyboardButton('15 minutes', callback_data='15 minutes'))

    bot.reply_to(message, "Please choose the candle expiration time:", reply_markup=markup)
