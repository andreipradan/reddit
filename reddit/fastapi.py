import hashlib
import hmac
import logging
import socket
import subprocess
from typing import Optional

import dotenv
import telegram
import uvicorn
from fastapi import FastAPI, status, Request


app = FastAPI()
logging.basicConfig(format="%(asctime)s - %(levelname)s:%(name)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def validate_signature(data, secret, headers):
    sig_header = 'X-Hub-Signature-256'
    if sig_header not in headers:
        return False
    computed_sign = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
    _, signature = headers[sig_header].split("=")
    return hmac.compare_digest(signature, computed_sign)


def run_cmd(cmd, bot, chat_id, host_name):
    logger.debug(f"Running {cmd}")
    process = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        logger.warning(f"Error: {error}")
        bot.send_message(
            chat_id=chat_id,
            text=f"[{host_name}] Error while trying to pull new changes from github {error}"
        ).to_json()
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
        breakpoint()
        return bot.send_message(
            chat_id=chat_id,
            text=f"[{host_name}] Got bad signature in request"
        )

    output = run_cmd("git pull", bot, chat_id, host_name)
    if not output:
        return bot.send_message(chat_id=chat_id, text=f"[{host_name}] Error at git pull")
    if output == b'Already up to date.\n':
        return bot.send_message(
            chat_id=chat_id,
            text=f"[{host_name}] No changes detected at git pull."
        )
    if run_cmd("systemctl restart reddit.service", bot, config["DEBUG_CHAT_ID"], host_name):
        return bot.send_message(chat_id=chat_id, text=f"[{host_name}] Reddit deployed successfully")

    return ""


def start():
    uvicorn.run(
        "reddit.fastapi:app",
        host="0.0.0.0",
        port=7777,
        reload=True
    )
