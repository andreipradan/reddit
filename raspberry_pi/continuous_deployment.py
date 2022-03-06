import logging

from reddit.fastapi import run_cmd
from raspberry_pi import github_hook
from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


def setup():
    run_cmd("sudo ./raspberry_pi/set-services.sh", silent=False)
    set_hook()
    logger.info("Completed setup, showing logs. CTRL+C to terminate")


def set_hook():
    github_hook.set_url()
