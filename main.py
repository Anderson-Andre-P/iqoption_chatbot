from flask import Flask
import telegram_bot
import config
import threading

app = Flask(__name__)

def run_bot():
    telegram_bot.bot.polling(none_stop=True)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(debug=True)

