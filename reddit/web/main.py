import logging

import dotenv
import sentry_sdk
import uvicorn
from fastapi import FastAPI

from reddit.settings import LOGGING_FORMAT
from reddit.web import github_hook, telegram_hook

sentry_sdk.init(dotenv.dotenv_values()["SENTRY_URL"], traces_sample_rate=1.0)
app = FastAPI()

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app.include_router(github_hook.router)
app.include_router(telegram_hook.router)


def start():
    uvicorn.run("reddit.web.main:app", port=7777, reload=True)
