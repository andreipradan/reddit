import logging
from pathlib import Path

import dotenv
import github
import requests
import telegram
from requests.exceptions import ConnectionError

from reddit.settings import LOGGING_FORMAT
from reddit.utils import run_cmd

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def copy_services():
    dest = "/etc/systemd/system"
    services_dir = Path(__file__).resolve().parent / "services"
    services = map(str, filter(Path.is_file, Path(services_dir).iterdir()))
    run_cmd(f"sudo cp {' '.join(services)} {dest}")
    logger.info(f"Copied services to {dest}")


def full_setup():
    run_cmd("/home/pi/.poetry/bin/poetry install")
    permissions = "pi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart reddit"
    run_cmd(f'echo "{permissions}" > /etc/sudoers.d/pi', silent=False)
    copy_services()
    run_cmd("sudo systemctl daemon-reload")
    start_services()
    run_cmd("sudo systemctl enable challonge.service fastapi.service ngrok.service reddit.service")
    logger.info("Completed setup! >> ./deploy/show-logs.sh")


def get_ngrok_url():
    try:
        resp = requests.get("http://localhost:4040/api/tunnels").json()
    except ConnectionError:
        raise ConnectionError("Failed to get ngrok tunnels. Is ngrok running?")

    for tunnel in resp["tunnels"]:
        url = tunnel["public_url"]
        if url.startswith("https://"):
            logger.info(f"Got ngrok URL: {url}")
            return url

    raise LookupError("Tunnel URL not found")


def start_services():
    run_cmd("sudo systemctl restart challonge fastapi ngrok reddit")


def set_url():
    env = dotenv.dotenv_values()
    ngrok_url = get_ngrok_url()
    g = github.Github(env["GITHUB_ACCESS_TOKEN"])
    hook_config = {
        "name": "web",
        "config": {
            "url": f"{ngrok_url}/github/",
            "content_type": "json",
            "secret": env["GITHUB_SECRET"],
        },
        "events": ["push"],
        "active": True,
    }
    repository = g.get_repo(f"{env['GITHUB_USERNAME']}/{env['GITHUB_REPOSITORY']}")
    hooks = repository.get_hooks()

    logger.warning(f"Deleting all hooks [{hooks.totalCount}]")
    for hook in hooks:
        hook.delete()

    hook = repository.create_hook(**hook_config)
    logger.info(f"Github web hook created successfully: {hook}")
    bot = telegram.Bot(token=env["TOKEN"])
    logger.info(f"Set telegram webhook: {bot.set_webhook(f'{ngrok_url}/telegram/')}")
