#!/bin/bash

# Discord到微信桥接器启动脚本

echo "🚀 启动Discord到微信桥接器..."

# 检查配置文件是否已设置实际的Discord频道
if grep -q "https://discord.com/channels/[0-9]" config.py; then
    python3 discord_to_wechat.py
else
    echo "⚠️  检测到config.py尚未配置"
    echo ""
    echo "请先编辑 config.py 文件："
    echo "1. 设置 DISCORD_CHANNEL_URLS（Discord频道URL列表）"
    echo "2. 根据 SENDER_TYPE 配置对应的参数"
    echo "   - wechat: 设置 WECHAT_RECEIVER_NAME"
    echo "   - enterprise_wechat: 设置 ENTERPRISE_WECHAT_WEBHOOK"
    echo ""
    echo "配置完成后再次运行: ./start.sh"
fi

