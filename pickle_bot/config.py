from dataclasses import dataclass
import logging
import os
import sys


from dotenv import dotenv_values


logger = logging.getLogger(__name__)


@dataclass
class Config:
    token: str
    log_level: str


def get_configuration() -> Config:
    environment = {
        **dotenv_values(".env"),
        **dotenv_values(".env.dev"),
        **os.environ,
    }

    required_variables = [
        "BOT_TOKEN",
    ]
    is_valid = True
    for variable in required_variables:
        if variable not in environment:
            logger.error(f"Missing required environment variable {variable!r}")
            is_valid = False
    if not is_valid:
        sys.exit(1)

    optional_variables = {"BOT_LOG_LEVEL": "INFO"}
    for variable, default in optional_variables.items():
        if variable not in environment:
            logger.warn(f"Missing environment variable {variable!r}, using default {default!r}")
            environment[variable] = default

    return Config(
        token=environment["BOT_TOKEN"],
        log_level=environment["BOT_LOG_LEVEL"],
    )
