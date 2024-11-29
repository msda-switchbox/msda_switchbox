FROM python:3.12-slim
LABEL maintainer="edenceHealth NV <info@edence.health>"

ARG AG="apt-get -yq --no-install-recommends"
ARG DEBIAN_FRONTEND="noninteractive"
RUN set -eux; \
  $AG update; \
  $AG install \
    ca-certificates \
    curl \
  ; \
  # install docker client + compose
  mkdir -m 0755 -p /etc/apt/keyrings; \
  KEYFILE="/etc/apt/keyrings/docker.asc"; \
  curl -fsSL -o "$KEYFILE" "https://download.docker.com/linux/debian/gpg"; \
  printf 'deb [arch=%s signed-by=%s] %s %s %s\n' \
    "$(dpkg --print-architecture)" \
    "$KEYFILE" \
    "https://download.docker.com/linux/debian" \
    "$(awk -F= '/VERSION_CODENAME/ {print $2}' /etc/os-release)" \
    "stable" \
    | tee /etc/apt/sources.list.d/docker.list; \
  $AG update; \
  $AG install \
    docker-buildx-plugin \
    docker-ce-cli \
    docker-compose-plugin \
  ; \
  # cleanup
  $AG clean; \
  $AG autoremove; \
  $AG autoclean; \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*;

COPY requirements.txt after_runner.sh /
RUN pip install --progress-bar=off -r /requirements.txt

COPY src/switchbox /app/switchbox
ENV PYTHONPATH="/app"

ENTRYPOINT [ "python3", "-m", "switchbox" ]

VOLUME [ "/data" ]
