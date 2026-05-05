#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ -z "${RENDER:-}" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
  "$PYTHON_BIN" -m venv .render-build-venv
  PYTHON_BIN=".render-build-venv/bin/python"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt

if [ "${INSTALL_LLM_KB:-false}" = "true" ]; then
  "$PYTHON_BIN" -m pip install "git+https://github.com/Techris93/llm-knowledge-base.git"
fi

if [ -f app/package.json ]; then
  npm --prefix app ci
  npm --prefix app run build
fi
