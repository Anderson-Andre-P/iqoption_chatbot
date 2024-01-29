import os
from flask import Flask
import telegram_bot
import config

app = Flask(__name__)

if __name__ == '__main__':
    if os.getenv('RUN_BOT', 'False') == 'True':
        telegram_bot.bot.polling(none_stop=True)
    if os.getenv('RUN_FLASK', 'False') == 'True':
        app.run(debug=True)
