"""healthz endpoint for serving a healthcheck"""

import logging

from flask import Blueprint, current_app

logger = logging.getLogger(__name__)
healthz = Blueprint("healthz", __name__)


@healthz.route("/")
def get_version():
    """serve the version"""
    return {
        "message": f"This is version {current_app.config['VERSION']} of the application"
    }
