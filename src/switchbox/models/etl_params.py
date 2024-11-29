"""models for interacting with outside data"""

import logging
from typing import IO, Literal, Mapping, Optional, Self, Sequence, Union

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BoolParam(BaseModel):
    """boolean input parameter"""

    param_type: Literal["bool"]
    question: str
    default: Optional[bool] = None


class CSVParam(BaseModel):
    """csv file input parameter"""

    param_type: Literal["csv"]
    question: str
    columns: Optional[Sequence[str]] = None


class FileParam(BaseModel):
    """regular file input parameter"""

    param_type: Literal["file"]
    question: str


class NumericParam(BaseModel):
    """numeric input parameter"""

    param_type: Literal["number"]
    question: str
    default: Optional[float | int] = None


class StringParam(BaseModel):
    """string input parameter"""

    param_type: Literal["str"]
    question: str
    default: Optional[str] = None


class ETLParams(BaseModel):
    """parameters specification (typically converted from yaml)"""

    params: Mapping[
        str,
        Union[BoolParam | CSVParam | FileParam | NumericParam | StringParam],
    ]

    @classmethod
    def from_yaml(cls, yaml_fh: IO[str]) -> Self:
        """
        return an instance initialized from the yaml content in the given
        file/io handle
        """
        return cls(**yaml.safe_load(yaml_fh))
