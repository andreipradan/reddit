import logging

import dotenv
import github
import requests

from reddit.settings import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_ngrok_url():
    try:
        json = requests.get("http://localhost:4040/api/tunnels").json()
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError("Failed to get ngrok tunnels. Is ngrok running?")

    for tunnel in json["tunnels"]:
        url = tunnel["public_url"]
        if url.startswith("https://"):
            logger.info(f"Got ngrok URL: {url}")
            return url

    raise LookupError("Tunnel URL not found")


def set_url():
    env = dotenv.dotenv_values()
    repo, token, user = env["GITHUB_REPOSITORY"], env["GITHUB_ACCESS_TOKEN"], env["GITHUB_USERNAME"]
    g = github.Github(token)
    hook_config = {
        "name": "web",
        "config": {
            "url": f"{get_ngrok_url()}/github/",
            "content_type": "json",
            "secret": env["GITHUB_SECRET"],
        },
        "events": ["push"],
        "active": True,
    }
    repository = g.get_repo(f"{user}/{repo}")
    hooks = repository.get_hooks()

    logger.warning(f"Deleting all hooks [{hooks.totalCount}]")
    for hook in hooks:
        hook.delete()

    logger.info("Creating new web hook")
    hook = repository.create_hook(**hook_config)
    logger.info(f"Web hook created successfully: {hook}")
