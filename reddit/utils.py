import hashlib
import hmac
import logging
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def validate_signature(data, secret, headers):
    sig_header = 'X-Hub-Signature-256'
    if sig_header not in headers:
        return False
    computed_sign = hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
    _, signature = headers[sig_header].split("=")
    return hmac.compare_digest(signature, computed_sign)


def run_cmd(cmd, silent=True):
    logger.debug(f"Running {cmd}")
    process = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        logger.warning(f"Error: {error}")
        if not silent:
            raise ValueError(error)
        return

    logger.debug(f"Output: {output}")
    if not (silent or output):
        raise ValueError(f"No output from running '{cmd}' [silent={silent} Output: {output}]")
    return output
