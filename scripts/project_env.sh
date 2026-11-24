#!/usr/bin/env bash
# 仅为本次命令及其子进程设置项目缓存，不修改用户的全局环境配置。
set -euo pipefail
# 从脚本位置确定项目根目录，支持从其他工作目录调用。
clinical_project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
# 没有待执行命令时给出简短用法。
if [[ $# -eq 0 ]]; then
    # 用标准错误说明如何通过本包装器运行命令。
    printf 'Usage: bash scripts/project_env.sh COMMAND [ARGS...]\n' >&2
    # 参数缺失时不执行任何下载或模型加载。
    exit 2
fi
# Hugging Face主目录放入已由Git忽略的项目cache目录。
export HF_HOME="${clinical_project_root}/cache/huggingface"
# 下载命令与Transformers使用同一个Hub文件缓存。
export HF_HUB_CACHE="${HF_HOME}/hub"
# 兼容仍读取旧Hub变量名的依赖。
export HUGGINGFACE_HUB_CACHE="${HF_HUB_CACHE}"
# Xet下载后端的分块和日志同样放入项目。
export HF_XET_CACHE="${HF_HOME}/xet"
# Hugging Face辅助资产缓存也放入项目。
export HF_ASSETS_CACHE="${HF_HOME}/assets"
# Sentence Transformers加载路径与hf download保持一致。
export SENTENCE_TRANSFORMERS_HOME="${HF_HUB_CACHE}"
# 其他遵循XDG约定的运行缓存放入项目。
export XDG_CACHE_HOME="${clinical_project_root}/cache/xdg"
# Torch下载缓存同样使用项目路径。
export TORCH_HOME="${clinical_project_root}/cache/torch"
# 将目标命令作为独立进程运行，调用方终端环境不会被这些export改变。
exec "$@"
