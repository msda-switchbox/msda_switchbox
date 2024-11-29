"""central declarative configuration for switchbox itself"""

from pathlib import Path

from basecfg import BaseCfg, opt


class Config(BaseCfg):
    """declarative app config class for switchbox"""

    log_level: str = opt(
        default="INFO",
        doc="set the verbosity of the console logs",
        choices=[
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
        ],
    )
    log_dir: Path = opt(
        default=Path("log"),
        doc="directory where job logs should be written",
    )
    debug: bool = opt(
        default=False,
        doc="run the app in debug mode",
    )
    version: str = opt(
        default="1.0.0",
        doc="ETL version",
    )
    job_dir: Path = opt(
        default=Path("/data/jobs"),
        doc="directory where file uploads are stored",
    )
    apimode: bool = opt(
        default=False,
        doc=(
            "whether to operate in api mode, this is used internally as part "
            "of the startup process"
        ),
    )
    port: int = opt(
        default=8000,
        doc="the network port to expose the services on",
    )
