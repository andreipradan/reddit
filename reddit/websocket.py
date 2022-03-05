import asyncio
import json
import logging

import dotenv
import requests
import telegram
import websockets

logging.basicConfig(format="%(asctime)s - %(levelname)s:%(name)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_socket_url(info_url):
    logger.debug("Fetching socket url...")
    response = requests.get(info_url, headers={'User-agent': 'reddit-live-telegram-bot'})
    if response.status_code == 429:
        return logger.error(f"Got 429: {response.json()['message']}")

    url = response.json()["data"]["websocket_url"]
    logger.debug(f"Got: {url}")
    return url


async def websocket(bot, chat_id, socket_url):
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
    config = dotenv.dotenv_values()
    bot = telegram.Bot(token=config["TOKEN"])
    chat_id = config["CHAT_ID"]
    debug_chat_id = config["DEBUG_CHAT_ID"]
    socket_url = get_socket_url(config["INFO_URL"])
    if not socket_url:
        return bot.send_message(chat_id=debug_chat_id, text="Could not fetch web socket URL")

    try:
        bot.send_message(chat_id=debug_chat_id, text="Socket started")
        asyncio.get_event_loop().run_until_complete(websocket(bot, chat_id, socket_url))
    except KeyboardInterrupt:
        bot.send_message(chat_id=debug_chat_id, text="Socket stopped")
        logger.info("Done")
