from telebot import TeleBot
from constant import bot_token

bot = TeleBot(bot_token)


def send_notification_message(text: str) -> None:
    bot.send_message(342974404, text)
