import logging

from reddit.fastapi import run_cmd
from raspberry_pi import github_hook
from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)


def cd_setup():
    permissions = "pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart reddit.service"
    logger.info(run_cmd(f'echo "{permissions}" >> /etc/sudoers.d/pi', silent=False))
    logger.info(run_cmd("sudo ./raspberry_pi/copy-services.sh", silent=False))
    start_services()
    github_hook.set_url()
    logger.info("Completed setup, showing logs. CTRL+C to terminate")


def start_services():
    logger.info(run_cmd("sudo ./raspberry_pi/start-services.sh", silent=False))


def show_logs():
    logger.info(run_cmd("./raspberry_pi/show-logs.sh", silent=False))
