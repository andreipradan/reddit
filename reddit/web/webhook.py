import logging
import socket

import dotenv
import telegram
from fastapi import APIRouter, status, Request, HTTPException

from reddit.utils import validate_signature, run_cmd

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@router.post("/github/", status_code=status.HTTP_200_OK)
async def process_github_webhook(request: Request):
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

    output = run_cmd("git pull origin main")
    if not output:
        return bot.send_message(
            chat_id=chat_id, text=f"[{host_name}] Could not git pull"
        )
    if output.strip() == b"Already up to date.":
        return bot.send_message(
            chat_id=chat_id, text=f"[{host_name}] [git pull] No new changes"
        )
    if output.strip().startswith(b"CONFLICT"):
        return bot.send_message(
            chat_id=chat_id, text=f"[{host_name}] [git pull] Conflict"
        )

    run_cmd("sudo /usr/bin/systemctl restart reddit")
    return bot.send_message(
        chat_id=chat_id, text=f"[{host_name}] Reddit deployed successfully"
    )
