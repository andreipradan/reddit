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
    show_logs()


def show_logs():
    cmd = "journalctl --follow " \
          "_SYSTEMD_UNIT=fastapi.service + " \
          "_SYSTEMD_UNIT=ngrok.service + " \
          "_SYSTEMD_UNIT=reddit.service"
    logger.info(f"Running {cmd}")
    process = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc
