"""entrypoint for execution"""

import logging
import os
import sys
from pathlib import Path

import baselog

from .compose import Compose
from .config import Config
from .flaskapp import create_app


def boot_switchbox(logger: logging.Logger, config: Config):
    """
    this function starts switchbox itself from the internal compose file in the
    subdeployment directory; this is the 2nd stage of the bootstrap process
    """
    c = Compose(
        project_dir=Path(os.path.join(os.path.dirname(__file__), "subdeployment")),
        project_name="switchbox",
        default_env={"TRAEFIK_PORT": str(config.port)},
    )

    for service in ("ui", "api", "ares", "cdmdb"):
        logger.info("starting %s", service)
        c.up(service)
    logger.info("background services started; exiting")


def main() -> int:
    """primary entrypoint; return int for sys.exit"""
    config = Config(
        prog=__package__,
        prog_description="MS Data Alliance ETL runner",
    )
    logger = baselog.BaseLog(
        root_name=__package__,
        log_dir=config.log_dir,
        console_log_level=config.log_level,
    )
    config.logcfg(logger)

    if not config.apimode:
        # start the other containers and exit
        boot_switchbox(logger, config)
        return 0

    # if we're still here we're in API mode, meaning we've been started from
    # the subdeployment directory; in API mode we act as a backing service for
    # the switchbox_ui

    app = create_app(config)

    # if you want to change which port the end-users browse to, see config.port
    app.run(host="0.0.0.0", port=8000, debug=config.debug)  # nosec B104

    return 0


if __name__ == "__main__":
    sys.exit(main())
