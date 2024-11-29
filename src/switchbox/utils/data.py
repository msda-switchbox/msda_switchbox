"""access to config resources embedded in the python source"""

import logging
from importlib import resources

from ..models import ETLParams

logger = logging.getLogger(__name__)

data_dir = resources.files("switchbox.data")


def get_etl_input_params():
    """return the parsed values from the etl_params.yml file in the data_dir"""
    params_yaml = data_dir / "etl_params.yml"
    with params_yaml.open("rt", encoding="utf-8") as f:
        return ETLParams.from_yaml(f)
