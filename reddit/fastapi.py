import logging
import socket

import dotenv
import telegram
import uvicorn
from fastapi import FastAPI, status, Request, HTTPException

from reddit.settings import LOGGING_FORMAT
from reddit.utils import validate_signature, run_cmd

app = FastAPI()
logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.post("/github/", status_code=status.HTTP_201_CREATED)
async def add_item(request: Request):
    config = dotenv.dotenv_values()
    bot = telegram.Bot(token=config["TOKEN"])
    chat_id = config["DEBUG_CHAT_ID"]
    host_name = socket.gethostname()

    if not validate_signature(
        await request.body(), config["GITHUB_SECRET"], request.headers
    ):
        bot.send_message(chat_id=chat_id, text=f"[{host_name}] Invalid hook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    output = run_cmd("git reset --hard origin/main")
    if not output:
        return bot.send_message(
            chat_id=chat_id, text=f"[{host_name}] Could not git pull"
        )
    if output.strip() == b"Already up to date.":
        return bot.send_message(
            chat_id=chat_id, text=f"[{host_name}] [git pull] No new changes"
        )
    if output.strip().startswith(b"CONFLICT"):
        return bot.send_message(chat_id=chat_id, text=f"[{host_name}] [git pull] Conflict")

    run_cmd("sudo /usr/bin/systemctl restart reddit")
    return bot.send_message(
        chat_id=chat_id, text=f"[{host_name}] Reddit deployed successfully"
    )


def start():
    uvicorn.run("reddit.fastapi:app", port=7777, reload=True)
