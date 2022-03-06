import asyncio
import json
import logging
import signal
import socket
import sys

import dotenv
import requests
import telegram
import websockets

from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config = dotenv.dotenv_values()

bot = telegram.Bot(token=config["TOKEN"])
chat_id = config["CHAT_ID"]
debug_chat_id = config["DEBUG_CHAT_ID"]
host_name = socket.gethostname()


def get_socket_url():
    logger.debug("Fetching socket url...")
    response = requests.get(config["INFO_URL"], headers={'User-agent': 'reddit-live-telegram-bot'})
    if response.status_code == 429:
        return logger.error(f"Got 429: {response.json()['message']}")

    url = response.json()["data"]["websocket_url"]
    logger.debug(f"Got: {url}")
    return url


def handle_sigterm(*_):
    stopped_message = f"[{host_name}] Socket stopped"
    bot.send_message(chat_id=debug_chat_id, text=stopped_message)
    logger.warning(stopped_message)
    sys.exit(0)


async def websocket(socket_url):
    async with websockets.connect(socket_url) as socket:
        logger.info("Connected to live thread!")
        last_payload, last_update = None, None
        while True:
            response = json.loads(await socket.recv())
            response_type = response['type']
            logger.debug(f"Got a new '{response_type}'")
            if response_type == "update":
                body = response["payload"]["data"]["body"]
                if last_update != body:
                    logger.info(body)
                    last_update = body
                    bot.send_message(chat_id=chat_id, text=body, disable_notification=True)
            elif response_type == "complete":
                text = "This thread is done. No more updates"
                logger.warning(text)
                bot.send_message(chat_id=chat_id, text=text, disable_notification=True)
                break


def start():
    signal.signal(signal.SIGTERM, handle_sigterm)
    socket_url = get_socket_url()
    if not socket_url:
        return bot.send_message(chat_id=debug_chat_id, text="Could not fetch web socket URL")

    bot.send_message(chat_id=debug_chat_id, text=f"[{host_name}] Socket started")
    try:
        asyncio.get_event_loop().run_until_complete(websocket(socket_url))
    except KeyboardInterrupt:
        handle_sigterm()
