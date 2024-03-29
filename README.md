<h1 align="center">LacustreBot</h1>

<p align="center">
  <a href="https://github.com/Anderson-Andre-P/lacustrebot">
    <img alt="Made by Anderson André" src="https://img.shields.io/badge/-Github-3D7BF7?style=for-the-badge&logo=Github&logoColor=white&link=https://github.com/Anderson-Andre-P" />
  </a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/lacustrebot-18.01.2024-3D7BF7?style=for-the-badge&labelColor=3D7BF7">
</p>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0; 
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-executing-project">Executing Project</a>
</p>

## :dart: About

**LacustreBot** LacustreBot is a Telegram bot designed to assist in trading and analysis in the financial market. With a variety of features and integration with brokers like IQ Option or ExNova, LacustreBot offers a comprehensive solution for traders and investors.

**Main Features:**

1. **Key generation for sale**

2. **Connection with the broker, iq Option or exnova with my affiliate link**

3. **Entry delay**

4. **Entry value**

5. **Set minimum payment**

6. **Gale strategy:** Gale quantity, gale multiplier

7. **Candlestick trend analysis**

8. **Group connection to capture entries sent in any OB group**

9. **Option to add a ready-made list too**

10. **Bot for Telegram**

**Benefits:**

- **Trading Efficiency:** LacustreBot automates several stages of the trading process, including generating sales keys, analyzing news and executing trades. This saves traders time and effort, allowing them to focus on more advanced trading strategies.

- **Real-time Market Analysis:** The bot provides real-time market analysis based on candlesticks and trend indicators. This helps traders make informed decisions about when and how to trade, improving their chances of success.

- **Flexibility and Customization:** LacustreBot offers customizable settings such as entry delay, entry amount, minimum payment and number of Gale operations. Traders can adapt the bot to their individual preferences and trading strategies.

- **Integration with Trading Groups:** The ability to connect to trading groups allows traders to receive and share information about trading opportunities in real time. This promotes collaboration and the exchange of knowledge between group members.

These combined benefits make LacustreBot a powerful tool for traders and investors who want to improve their efficiency, make informed decisions, and stay up to date on the latest financial market trends.

## :rocket: Technologies

The project was developed using the following technologies and tools:

- Python
- Telegram Bot
- Telebot
- Flask
- IQ Option API

## :rocket: Archteture

```bash
- lacustrebot/
  - iqoptionapi/
  - .gitignore
  - config.py
  - iqoption.py
  - main.py
  - README.md
  - telegram_bot.py
  - utils.py
```

### Description of archteture

In the lacustrebot folder you have all the necessary files to make the bot work!

The iqoptionapi folder is provided on GitHub of the IQ Option API, it is quite extensive and necessary because it contains the endpoints for making login requests, user validation, pulling data, sending data, etc. Do not touch it and, if necessary, get the complete file from the [official repository](https://github.com/iqoptionapi/iqoptionapi).

The config.py file only contains the settings necessary for the bot to work, in this case it is just the token that I chose to make available so that you can show it to the client. I emphasize that creating it is simple, just [follow this bot father tutorial](https://core.telegram.org/bots/tutorial).

The iqoption.py file is responsible for the main IQ Option functions that are used (connect and buy).

The main.py file is the initial one for the application, it is what you run to make the bot work on Telegram.

The telegram_bot.py file is used to "store" the bot's functions and their respective commands. In the future, it would be ideal to remove the commands from this file and leave only the functions so that the algorithm has greater maintainability.

The utils.py file has the helper functions that can be used in various parts of the code.

## :checkered_flag: Executing Project

To run the LacustreBot project on your computer, follow the steps below using the terminal or command prompt:

```bash
# Clone the repository to your local machine
$ git clone git@github.com:Anderson-Andre-P/lacustrebot.git

# Navigate to the project directory
$ cd './lacustrebot'

# Create a virtual environment (optional but recommended)
$ python -m venv venv

# Activate the virtual environment (Linux/macOS)
$ source venv/bin/activate

# Activate the virtual environment (Windows)
$ venv\Scripts\activate

# Install the required dependencies
$ pip install -r requirements.txt

# Run the main.py file to start the LacustreBot
$ python main.py
```

<a href="#top">Back to top</a>
