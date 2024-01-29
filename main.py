from flask import Flask
import telegram_bot
import config

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

def run_bot():
    telegram_bot.bot.polling(none_stop=True)

if __name__ == '__main__':
    run_bot()

    app.run(debug=True)
