#!/bin/bash
set -e

# 显示环境信息
python --version
which python || true

# 修复部分环境字体缺失导致的渲染问题
export FONTCONFIG_PATH=/etc/fonts

# 启动应用
exec python /app/discord_to_wechat.py
