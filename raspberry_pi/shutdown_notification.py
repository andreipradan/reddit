import socket

import dotenv
import telegram


def notify():
    env = dotenv.dotenv_values()
    bot = telegram.Bot(token=env["TOKEN"])
    host_name = socket.gethostname()
    bot.send_message(chat_id=env["DEBUG_CHAT_ID"], text=f"[{host_name}] Socket stopped. [Shutdown]")
