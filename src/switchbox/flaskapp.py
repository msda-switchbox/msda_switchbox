"""flask app definition"""

import logging
import os

# from celery import Celery
from flask import Blueprint, Flask

from .blueprints import healthz, job, params
from .config import Config

logger = logging.getLogger(__name__)


def create_app(config: Config):
    """Create and configure the app"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping({key.upper(): getattr(config, key) for key in config})

    api = Blueprint("api", __name__, url_prefix="/api")
    api.register_blueprint(healthz, url_prefix="/healthz")
    api.register_blueprint(job, url_prefix="/job")
    api.register_blueprint(params, url_prefix="/params")
    app.register_blueprint(api)

    # celery = Celery("hello", broker="amqp://guest@localhost//")

    logger.error("app instance path: %s", app.instance_path)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
