import hashlib
import hmac
import logging
import socket
import subprocess

import dotenv
import telegram
import uvicorn
from fastapi import FastAPI, status, Request

from reddit.settings import LOGGING_FORMAT

app = FastAPI()
logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def validate_signature(data, secret, headers):
    sig_header = 'X-Hub-Signature-256'
    if sig_header not in headers:
        return False
    computed_sign = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
    _, signature = headers[sig_header].split("=")
    return hmac.compare_digest(signature, computed_sign)


def run_cmd(cmd, silent=True):
    logger.debug(f"Running {cmd}")
    process = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        logger.warning(f"Error: {error}")
        if not silent:
            raise ValueError(error)
        return
    logger.debug(f"Output: {output}")
    return output


@app.post("/github/", status_code=status.HTTP_201_CREATED)
async def add_item(request: Request):
    config = dotenv.dotenv_values()
    bot = telegram.Bot(token=config["TOKEN"])
    chat_id = config["DEBUG_CHAT_ID"]
    host_name = socket.gethostname()

    if not validate_signature(await request.body(), config["GITHUB_SECRET"], request.headers):
        logger.error(f"Invalid signature")
        return bot.send_message(
            chat_id=chat_id,
            text=f"[{host_name}] Got bad signature in request"
        )

    logger.info("Got new updates")
    output = run_cmd("git pull")
    if not output:
        return bot.send_message(chat_id=chat_id, text=f"[{host_name}] Error at git pull")
    if output == b'Already up to date.\n':
        return bot.send_message(
            chat_id=chat_id,
            text=f"[{host_name}] No changes detected at git pull."
        )
    run_cmd("/usr/bin/systemctl restart reddit.service")
    return bot.send_message(chat_id=chat_id, text=f"[{host_name}] Reddit deployed successfully")


def start():
    uvicorn.run(
        "reddit.fastapi:app",
        host="0.0.0.0",
        port=7777,
        reload=True
    )
