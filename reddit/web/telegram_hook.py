import logging
import os

import dotenv
import six
import telegram
from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import exceptions
from google.cloud import translate_v2 as translate
from sentry_sdk import start_transaction, start_span

from fastapi import APIRouter, status, Request

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config = dotenv.dotenv_values()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["GOOGLE_APPLICATION_CREDENTIALS"]


@router.post("/telegram/", status_code=status.HTTP_200_OK)
async def process_telegram_webhook(request: Request):
    whitelist = config["WHITELIST"].split(",") + ["andreierdna"]
    bot = telegram.Bot(token=config["TOKEN"])

    json = await request.json()
    update = telegram.Update.de_json(json, bot)
    message = update.message

    if not hasattr(message, "text"):
        logging.warning(f"got no text")
        return ""

    text = message.text
    if text and message.from_user.username not in whitelist:
        logging.error(f"Ignoring message from: {message.from_user.username or message.from_user.id}")
        return ""

    if not message.forward_date:
        logging.warning("Ignoring message, not a forward")
        return ""

    text = text or update.message.caption
    if not text:
        logging.warning("No text nor caption provided")
        return ""

    text_max_size = int(config["TEXT_MAX_SIZE"])
    text_size = len(text)
    if text_size > text_max_size:
        logging.warning(f"Exceeded {text_max_size} characters: {text_max_size}")
        with start_transaction(op="telegram", name="too_many_chars"):
            return bot.send_message(
                chat_id=message.chat_id,
                text=f"Too many characters. Try sending less than {text_max_size} characters",
            ).to_json()

    if not text.strip():
        logging.warning(f"No text after stripping: {text}")
        return ""

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    try:
        translate_client = translate.Client()
    except DefaultCredentialsError as e:
        logging.error(e)
        return ""

    with start_transaction(op="translate", name="Translate with Google"):
        with start_span(op="http", description="translate") as span:
            try:
                result = translate_client.translate(text, target_language="en", format_="text")
            except (GoogleAPICallError, exceptions.BadRequest) as e:
                logging.error(e)
                return "Something went wrong. For usage and examples type '/translate help'."
            detected_language = result["detectedSourceLanguage"] or "-"
            span.set_tag("detected_language", detected_language)

        with start_span(op="telegram", description="Send translation on telegram"):
            return bot.send_message(
                chat_id=message.chat_id,
                text=f"[{detected_language}] {result['translatedText']}",
            ).to_json()
