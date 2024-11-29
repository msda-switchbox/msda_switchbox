"""params endpoint which gives the UI a list of input values the ETL requires"""

import logging

from flask import Blueprint, make_response

from ..utils.data import get_etl_input_params

logger = logging.getLogger(__name__)
params = Blueprint("params", __name__)


@params.route("/", methods=["GET"])
def get_etl_params():
    """return the params yaml document as json"""
    # something about flask's internal jsonification mangles key order when we
    # just return model_dump() so we need to jsonify ourselves using the
    # pydantic json dumper
    response = make_response(get_etl_input_params().model_dump_json())
    response.headers["Content-Type"] = "application/json"
    return response
