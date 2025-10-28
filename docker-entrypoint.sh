#!/bin/bash
set -e

# 显示环境信息
python --version
which python || true

# 若未配置 DISCORD_CHANNEL_URLS/WECHAT/WEBHOOK，仍允许启动，由程序内部校验

# 持久化 Chrome 用户数据目录（保存 Discord 登录状态）
export CHROME_USER_DATA_DIR="/app/chrome_data"
mkdir -p "$CHROME_USER_DATA_DIR"

# 显式设置无头运行参数（程序内也会设置，这里提供环境兼容）
export CHROME_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu --window-size=1920,1080 --user-data-dir=$CHROME_USER_DATA_DIR"

# 修复部分环境字体缺失导致的渲染问题
export FONTCONFIG_PATH=/etc/fonts

# 启动应用
exec python /app/discord_to_wechat.py
