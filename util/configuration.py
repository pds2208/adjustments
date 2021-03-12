import os

import toml

from util.logging import log


class ApplicationConfiguration:
    config = None

    @classmethod
    def init(cls):
        if cls.config is not None:
            return cls.config
        if os.environ.get("RUNTIME") == "development":
            log.info("Lewis & Wood Adjustments - Starting up - Development")
            cls.config = toml.load(os.path.join(os.path.dirname(__file__), "config-dev.toml"))
        else:
            log.info("Lewis & Wood Adjustments - Starting up - Production")
            cls.config = toml.load(os.path.join(os.path.dirname(__file__), "config-prod.toml"))
        return cls.config


config = ApplicationConfiguration.init()

app_timeout = config["app"]["timeout"]

# HyperSage configuration
hyper_uri = config["hyper_sage"]["uri"]
hyper_api_key = config["hyper_sage"]["api_key"]
hyper_timeout = config["hyper_sage"]["timeout"]

adjustments_uri = config["adjustments"]["adjustments_uri"]
sleep = config["app"]["sleep"]
database_uri = os.environ.get("DATABASE_URL")
