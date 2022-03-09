import logging

import uvicorn
from fastapi import FastAPI

from reddit.settings import LOGGING_FORMAT
from reddit.web import webhook

app = FastAPI()

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app.include_router(webhook.router)


def start():
    uvicorn.run("reddit.web.main:app", port=7777, reload=True)
