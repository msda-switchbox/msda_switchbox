"""models related to docker container jobs"""

import datetime
import json
import logging
import os
import subprocess  # nosec B404
import time
from pathlib import Path
from typing import (
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Self,
    Sequence,
    TypeAlias,
    Union,
)

from docker import APIClient
from pydantic import BaseModel

from ..compose import Compose

logger = logging.getLogger(__name__)


ParamInput: TypeAlias = Union[bool, float, int, str]

JobConfig: TypeAlias = Dict[str, Union[bool, float, int, str]]

ContainerStatus: TypeAlias = Literal[
    "created",
    "running",
    "paused",
    "restarting",
    "removing",
    "exited",
    "dead",
]


class JobItem(BaseModel):
    """container class for the list_jobs api call"""

    job_id: str
    start_datetime: datetime.datetime
    status: str
    source_name: str
    source_date: str


class JobDetail(BaseModel):
    """container class for the get_job api call"""

    id: str
    date: datetime.datetime
    status: str
    name: str
    vocabVersion: str
    sourceDate: str
    etlVersion: str
    cdmVersion: str
    log: str


def make_job_id() -> str:
    """generate a new job_id which can be used as a JobDir subdirectory"""
    return str(int(time.time()))


def inspect_container(container_id: str):
    """ask docker for the status of the given container"""
    client = APIClient()
    return client.inspect_container(container_id)


def list_jobs(base: Path) -> List[JobItem]:
    """list the JobItem(s) found in the given job directory"""
    result = []
    for subdir in base.iterdir():
        if not subdir.is_dir():
            logger.warning("unrecognized entity in job directory: %s", subdir)
            continue
        job_id = subdir.name
        job = Job.open(job_id, base)
        config = job.job_dir.get_config()
        status = job.job_dir.get_latest_status()

        result.append(
            JobItem(
                job_id=job_id,
                start_datetime=status.start_dt,
                status=status.status,
                source_name=str(config.get("cdm_source_name", "")),
                source_date=str(config.get("source_release_date", "")),
            )
        )
    return result


def get_job(base: Path, job_id: str) -> JobDetail:
    """get the data from the job with the given id in the given job directory"""
    job = Job.open(job_id, base)
    config = job.job_dir.get_config()
    status = job.job_dir.get_latest_status()
    log = job.job_dir.get_log()

    return JobDetail(
        id=job_id,
        date=status.start_dt,
        status=status.status,
        name=str(config.get("cdm_source_name", "")),
        vocabVersion="v5.0 31-AUG-23",
        sourceDate=str(config.get("source_release_date", "")),
        etlVersion="1.0.0",
        cdmVersion="5.4",
        log=log,
    )


class JobStatus(BaseModel):
    """file structure for job_dir status file"""

    container_id: Optional[Union[str, int]] = 0
    status: ContainerStatus = "created"
    exit_code: int = -255
    start_dt: datetime.datetime = datetime.datetime.min
    exit_dt: datetime.datetime = datetime.datetime.min


class MountRef(BaseModel):
    """named volume/bind-mount container"""

    host_path: str
    container_path: str
    mode: Literal["ro", "rw"] = "ro"


class JobDir(BaseModel):
    """util model for maintaining a fixed directory structure"""

    host_path: Path
    data_subdir: Path
    log_subdir: Path
    config_file: Path
    status_file: Path
    job_id: str

    @classmethod
    def open(cls, base_path: Path, job_id: str) -> Self:
        """create an instance for the given job_id"""
        host_path = base_path / Path(job_id)
        data_subdir = host_path / "data"
        log_subdir = host_path / "log"
        config_file = host_path / "config.json"
        status_file = host_path / "status.json"

        data_subdir.mkdir(parents=True, exist_ok=True)
        log_subdir.mkdir(parents=True, exist_ok=True)
        config_file.touch(exist_ok=True)
        status_file.touch(exist_ok=True)

        return cls(
            host_path=host_path,
            data_subdir=data_subdir,
            log_subdir=log_subdir,
            config_file=config_file,
            status_file=status_file,
            job_id=job_id,
        )

    def set_config(self, values: JobConfig):
        """replace the config file in the job_dir with the given values"""
        with open(self.config_file, "wt", encoding="utf-8") as cfgfh:
            json.dump(values, cfgfh, indent=2)

    def get_config(self) -> JobConfig:
        """the parsed contents of the job_dir config file"""
        json_data = ""
        with open(self.config_file, "rt", encoding="utf-8") as cfgfh:
            json_data = cfgfh.read()
            if json_data:
                return json.loads(json_data)
        return {}

    def get_latest_status(self) -> JobStatus:
        """get the status of a container (and ensure it is up-to-date info)"""
        saved_status = self.get_status()
        if not saved_status.container_id or saved_status.status == "exited":
            return saved_status

        container_info = inspect_container(str(saved_status.container_id).strip())

        saved_status.status = container_info["State"]["Status"]
        saved_status.exit_code = container_info["State"]["ExitCode"]
        saved_status.start_dt = container_info["State"]["StartedAt"]
        saved_status.exit_dt = container_info["State"]["FinishedAt"]

        self.set_status(saved_status)
        return saved_status

    def get_status(self) -> JobStatus:
        """returns the status of the job in the given job_dir"""
        with open(self.status_file, "rt", encoding="utf-8") as statusfh:
            raw_data = statusfh.read()
            if raw_data:
                json_data = json.loads(raw_data)
                return JobStatus(**json_data)
        return JobStatus()

    def get_log(self) -> str:
        """returns the text content of the etl job log"""
        # Ensure the directory exists and is a directory
        if not self.log_subdir.exists() or not self.log_subdir.is_dir():
            raise ValueError("log_subdir a valid directory")

        # Gather all text contents from files in the directory
        log_data = ""
        for file_path in self.log_subdir.iterdir():
            if file_path.is_file():
                with file_path.open("r", encoding="utf-8") as file:
                    log_data += file.read()

        return log_data

    def set_status(self, status: JobStatus):
        """returns the status of the job in the given job_dir"""
        with open(self.status_file, "wt", encoding="utf-8") as statusfh:
            statusfh.write(status.model_dump_json(indent=2))


class Job(BaseModel):
    """all information about a docker container job (config, status, output)"""

    # config
    job_id: str
    job_dir: JobDir
    environment: Mapping[str, ParamInput] = {}
    mounts: Sequence[MountRef] = []
    # status
    container_id: Optional[str] = None
    exit_code: Optional[int] = None
    status: Optional[JobStatus] = None

    @classmethod
    def open(
        cls,
        job_id: Optional[str] = None,
        base_path: Optional[Path] = None,
        mounts: Optional[Sequence[MountRef]] = None,
        container_id: Optional[str] = None,
        exit_code: Optional[int] = None,
        status: Optional[JobStatus] = None,
    ) -> Self:
        """return a new instance of Job with the given values"""
        base_path = Path("/data/jobs") if not base_path else base_path
        job_id = make_job_id() if not job_id else job_id
        job_dir = JobDir.open(base_path, job_id)
        if not mounts:
            mounts = []

        environment = job_dir.get_config()

        status = job_dir.get_latest_status()
        logger.debug("status: %s", status)

        return cls(
            job_id=job_id,
            job_dir=job_dir,
            environment=environment,
            mounts=mounts,
            container_id=container_id,
            exit_code=exit_code,
            status=status,
        )

    def start(self) -> JobStatus:
        """start the etl job"""

        project_dir = Path(
            os.path.normpath(
                os.path.join(os.path.dirname(__file__), "..", "subdeployment")
            )
        )

        c = Compose(
            project_dir=project_dir,
            project_name="switchbox",
        )
        environment = {
            "LOG_DIR": str(self.job_dir.log_subdir),
            "DATADIR": str(self.job_dir.data_subdir),
            "VOCAB_DIR": "/vocab",
            **{k.upper(): str(v) for k, v in self.job_dir.get_config().items()},
        }

        result = c.run(
            "etl",
            detach=True,
            env=environment,
        )
        container_id = result.stdout.strip()

        # after the etl exits we run ares
        start_afterrunner(
            container_id,
            str(project_dir),
            ["docker", "compose", "run", "--rm", "aresindexer"],
        )

        status = self.job_dir.get_status()
        status.container_id = container_id
        status.status = "running"
        self.job_dir.set_status(status)
        return status


def start_afterrunner(target_container_id: str, workdir: str, command: List[str]):
    """after the targeted container exits, cd to the given workdir and run the given command"""
    command = ["/after_runner.sh", target_container_id, workdir, *command]
    # pylint: disable=subprocess-popen-preexec-fn
    with subprocess.Popen(command, preexec_fn=os.setsid):  # nosec B603
        # using "with" here to control resource allocation (to make pylint happy)
        pass
