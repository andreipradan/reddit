import logging
import subprocess

from reddit.fastapi import run_cmd
from raspberry_pi.github_hook import set_url
from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


def setup():
    run_cmd("sudo ./raspberry_pi/set-services.sh", silent=False)
    set_url()
    logger.info("Completed setup, showing logs. CTRL+C to terminate")
