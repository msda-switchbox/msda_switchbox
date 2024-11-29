"""rest endpoint for CRUD operations on docker container jobs"""

import logging
from functools import cache
from pathlib import Path

from flask import Blueprint, current_app, request

from ..models.job import Job, get_job, list_jobs
from ..utils.data import get_etl_input_params

logger = logging.getLogger(__name__)
job = Blueprint("job", __name__)


@cache
def base_job_dir() -> Path:
    """helper function which returns the configured JOB_DIR"""
    return Path(current_app.config["JOB_DIR"])


@job.route("/", methods=["GET"])
def get_job_list():
    """list jobs currently on the system"""
    return {"jobs": [m.model_dump() for m in list_jobs(base_job_dir())]}


@job.route("/", methods=["POST"])
def create_job():
    """Create a new job"""

    # not specifying a job_id means we make a new job (and job_dir)
    newjob = Job.open(base_path=base_job_dir())

    request_data = request.form.to_dict()
    newjob.job_dir.set_config(request_data)

    params = get_etl_input_params()
    for param_name, param_value in params.params.items():
        logger.debug("incoming param %s (%s)", param_name, param_value.param_type)
        if param_value.param_type == "csv":
            if (file_data := request.files.get(param_name)) is not None:
                output_path = newjob.job_dir.data_subdir / f"{param_name}.csv"
                logger.debug("incoming file %s; writing to %s", param_name, output_path)
                file_data.save(output_path)

    # start the job
    status = newjob.start()

    return {"job_id": newjob.job_id, "status": status.model_dump()}


@job.route("/<job_id>", methods=["GET"])
def read_job(job_id: str):
    """get the contents of a job"""
    return get_job(base_job_dir(), job_id).model_dump()


@job.route("/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """delete the job with the given job_id"""
    logger.debug("passing on delete_job with id=%s", job_id)


@job.route("/<job_id>/stop", methods=["POST"])
def stop_job(job_id: int):
    """Stop etl job"""
    logger.debug("passing on stop with id=%s", job_id)
