from flask import Flask
import telegram_bot
import config

app = Flask(__name__)

if __name__ == '__main__':
    telegram_bot.bot.polling(none_stop=True)
    app.run(debug=True)
