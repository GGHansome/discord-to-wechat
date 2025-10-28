#!/bin/bash

# Discord到微信桥接器启动脚本

echo "🚀 启动Discord到微信桥接器..."

# 检查配置文件
if ! grep -q "服务器ID" config.py; then
    python3 discord_to_wechat.py
else
    echo "⚠️  检测到config.py尚未配置"
    echo ""
    echo "请先编辑 config.py 文件："
    echo "1. 设置 DISCORD_CHANNEL_URL（Discord频道URL）"
    echo "2. 设置 WECHAT_RECEIVER_NAME（微信接收者名称）"
    echo ""
    echo "配置完成后再次运行: ./start.sh"
fi

