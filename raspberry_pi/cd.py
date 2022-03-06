import logging

from reddit.fastapi import run_cmd
from raspberry_pi import github_hook
from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def cd_setup():
    permissions = "pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart reddit.service"
    output = run_cmd(f'echo "{permissions}" >> /etc/sudoers.d/pi', silent=False)
    if not output:
        raise ValueError("Could not copy permissions to sudoers.d/pi")
    logger.info(output)
    output = run_cmd("sudo ./raspberry_pi/scripts/copy-services.sh", silent=False)
    if not output:
        raise ValueError("Could not copy services to systemd")
    logger.info(output)
    start_services()
    github_hook.set_url()
    logger.info("Completed setup, showing logs. CTRL+C to terminate")
    show_logs()


def start_services():
    output = run_cmd("sudo ./raspberry_pi/scripts/start-services.sh", silent=False)
    if not output:
        raise ValueError("Could not start services")
    logger.info(output)


def show_logs():
    run_cmd("./raspberry_pi/scripts/show-logs.sh", silent=False)
