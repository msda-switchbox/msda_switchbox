"""infrastructure for running etls with docker compose"""

from pathlib import Path

from pydantic import BaseModel

from ..compose import Compose


class ETLConfig(BaseModel):
    """configuration for a compose run/up on an ETL"""

    vocab_dir: Path
    log_dir: Path
    datadir: Path
    cdm_source_name: str
    cdm_source_abbreviation: str
    cdm_holder: str
    source_release_date: str
    cdm_etl_ref: str
    input_delimiter: str
    reload_vocab: bool
    source_description: str
    source_doc_reference: str


def compose_run_etl(
    project_dir: Path,
    config: ETLConfig,
    service: str = "etl",
):
    """call docker compose run in the given project_dir for an ETL service"""
    dc = Compose(project_dir=project_dir)
    run = dc.run(
        service,
        env={
            "VOCAB_DIR": str(config.vocab_dir),
            "LOG_DIR": str(config.log_dir),
            "DATADIR": str(config.datadir),
            "CDM_SOURCE_NAME": config.cdm_source_name,
            "CDM_SOURCE_ABBREVIATION": config.cdm_source_abbreviation,
            "CDM_HOLDER": config.cdm_holder,
            "SOURCE_RELEASE_DATE": config.source_release_date,
            "CDM_ETL_REF": config.cdm_etl_ref,
            "INPUT_DELIMITER": config.input_delimiter,
            "RELOAD_VOCAB": "1" if config.reload_vocab else "",
            "SOURCE_DESCRIPTION": config.source_description,
            "SOURCE_DOC_REFERENCE": config.source_doc_reference,
        },
    )
    return run.stdout
