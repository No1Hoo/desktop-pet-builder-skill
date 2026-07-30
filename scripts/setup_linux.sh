#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$project_dir/.venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3。" >&2
  exit 1
fi

python3 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install --upgrade pip
"$venv_dir/bin/python" -m pip install -r \
  "$project_dir/examples/xiajie-desktop-pet/requirements.txt"

echo "Linux 运行环境已准备：$venv_dir"
echo "启动示例：$project_dir/启动霞姐桌宠.sh"
