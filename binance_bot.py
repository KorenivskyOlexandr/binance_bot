from telebot import TeleBot
from constant import bot_token, my_chat_id

bot = TeleBot(bot_token)


def send_notification_message(text: str) -> None:
    bot.send_message(my_chat_id, text)
