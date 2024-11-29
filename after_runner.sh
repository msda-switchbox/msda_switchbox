#!/bin/sh
# runs a command when the container with the given id exits (only if it exits 0)
# args:
#   1 = container id
#   2 = workdir
#   3... = command
set -eu
SELF=$(basename "$0" ".sh")

log() {
  printf '%s %s %s\n' "$(date '+%FT%T%z')" "$SELF" "$*" >&2
}

die() {
  log "FATAL:" "$@"
  exit 1
}

log "${SELF} starting as $(id) in $(pwd)"
container_id=${1:?container ID argument is required}; shift
work_dir=${1:?working directory argument is required}; shift
: "${1:?the command argument(s) are required}"

exit_code=$(docker wait "$container_id")
[ "$exit_code" != "0" ] && die "non-zero exit of target container"

cd "$work_dir" || die "unable to cd to ${work_dir}"

"$@" || die "non-zero exit from command"

log "exiting with success"
exit 0
