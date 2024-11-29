# msda_switchbox

A project of the [MS Data Alliance](https://www.msdataalliance.org/) and [edenceHealth](https://edence.health/)

## Connectivity Overview

```mermaid
flowchart TD
    user(("End User"))
    analytics["Analytics Tools\ne.g. datagrip, tableau"]
    browser["Browser\ne.g. Chrome & Firefox"]

    subgraph "docker"
        ares
        ares_data["Ares Output Files"]
        ares_indexer
        cdmdb
        msda_api
        msda_etl
        msda_ui
        traefik
    end

    user --> browser --> traefik
    traefik --> ares & msda_ui & msda_api & ares_data
    msda_etl --> cdmdb
    cdmdb --> ares_indexer --> ares_data
    msda_api --> msda_etl
    user --> analytics -----> cdmdb
```

## Notes

- Released under an open source license [LICENSE.txt](LICENSE.txt)
