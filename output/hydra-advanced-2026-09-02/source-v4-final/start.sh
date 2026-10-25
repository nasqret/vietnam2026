#!/bin/sh
set -eu

HYDRA_PLAYGROUND_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HYDRA_PLAYGROUND_PYTHON="$HYDRA_PLAYGROUND_DIR/.runtime/venv/bin/python3"
if [ ! -x "$HYDRA_PLAYGROUND_PYTHON" ]; then
  HYDRA_PLAYGROUND_PYTHON=$(command -v python3)
fi

exec "$HYDRA_PLAYGROUND_PYTHON" -I -B "$HYDRA_PLAYGROUND_DIR/server.py" --port "${HYDRA_PORT:-8767}"
