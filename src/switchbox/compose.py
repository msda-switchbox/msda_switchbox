"""subprocess-based interactions with the docker compose command"""

import logging
import os
import subprocess  # nosec B404
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeAlias

import docker
from pydantic import BaseModel, ConfigDict

EnvDict: TypeAlias = Optional[Dict[str, str]]
DockerClient: TypeAlias = docker.client.DockerClient
DockerContainer: TypeAlias = docker.models.containers.Container


logger = logging.getLogger(__name__)


class ComposeConfig(BaseModel):
    """container class for 'docker compose config' output"""

    model_config = ConfigDict(extra="allow")


class Compose:
    """interactions with 'docker compose' and docker"""

    project_dir: Path
    project_name: str
    docker: DockerClient
    default_env: EnvDict

    def __init__(
        self,
        project_dir: Path,
        project_name: Optional[str] = None,
        docker_client: Optional[DockerClient] = None,
        default_env: EnvDict = None,
    ) -> None:
        self.project_dir = project_dir
        self.project_name = project_name if project_name else project_dir.name
        self.docker = docker_client if docker_client is not None else docker.from_env()
        self.default_env = {} if default_env is None else default_env

    def compose(
        self,
        *subcmd: str,
        env: EnvDict = None,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        call a docker compose subcommand;
        """
        subprocess_env, _ = self.format_env(env)
        # note that we're not injecting --env flags to the command, so if they are
        # required those flags will need to be included in subcmd
        command = [
            "docker",
            "compose",
            f"--project-name={self.project_name}",
            f"--project-directory={self.project_dir}",
            *subcmd,
        ]
        logger.debug("running docker compose; command:%s; env:%s", command, env)
        return subprocess.run(  # nosec B603
            command,
            env=subprocess_env,
            capture_output=True,
            check=True,
            encoding="utf-8",
            cwd=cwd,
        )

    def ps(self) -> List[DockerContainer]:
        """
        get a list of docker container objects for all services in the compose
        file
        """
        result = self.compose("ps", "--all", "--quiet")
        return [
            self.docker.containers.get(container_id)
            for container_id in result.stdout.splitlines()
        ]

    def run(
        self,
        service_name: str,
        container_args: Optional[List[str]] = None,
        detach: bool = False,
        env: EnvDict = None,
        rm: bool = False,
        volumes: Optional[List[str]] = None,
    ) -> subprocess.CompletedProcess[str]:
        """call docker compose run"""
        subprocess_env, run_env_flags = self.format_env(env)
        flags = [
            "--quiet-pull",
            "--remove-orphans",
            "--service-ports",
            *run_env_flags,
        ]
        if rm:
            flags.append("--rm")
        if detach:
            flags.append("--detach")
        if volumes:
            for vol in volumes:
                flags.append(f"--volume={vol}")
        if container_args is None:
            container_args = []
        return self.compose(
            *[
                "run",
                *flags,
                service_name,
                *container_args,
            ],
            env=subprocess_env,
        )

    def up(
        self,
        service_name: str,
        env: EnvDict = None,
    ) -> subprocess.CompletedProcess[str]:
        """call docker compose up"""
        subprocess_env, up_env_flags = self.format_env(env)
        subcmd = [
            "up",
            "--detach",
            "--quiet-pull",
            "--remove-orphans",
            *up_env_flags,
            service_name,
        ]
        return self.compose(*subcmd, env=subprocess_env)

    def config(self) -> ComposeConfig:
        """call docker compose config"""
        return ComposeConfig.model_validate_json(
            self.compose(
                "config",
                "--format=json",
                "--resolve-image-digests",
            ).stdout
        )

    def format_env(self, env: EnvDict) -> Tuple[EnvDict, List[str]]:
        """
        given an Optional 'env' mapping of key/value envvar pairs, return a 2-tuple:
        0: a dict with the values from os.environ updated by the contents of 'env'
        1: a list of "docker compose run/up" flags like "--env=EXAMPLE_VAR" which
            tell compose to pass EXAMPLE_VAR from its environment into the
            container environment
        """
        subprocess_env_dict = None
        docker_env_flags = []
        if env is not None:
            subprocess_env_dict = os.environ.copy()
            if self.default_env is not None:
                subprocess_env_dict.update(self.default_env)
            subprocess_env_dict.update(env)
            docker_env_flags = [f"--env={key.upper()}" for key in env.keys()]
        return subprocess_env_dict, docker_env_flags
