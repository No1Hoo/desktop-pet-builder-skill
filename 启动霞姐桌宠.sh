#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
pet_dir="$project_dir/examples/xiajie-desktop-pet"
python_bin="$project_dir/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "桌宠运行环境不存在：$python_bin" >&2
  exit 1
fi

cd "$pet_dir"
exec "$python_bin" main.py
