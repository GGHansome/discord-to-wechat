#!/bin/bash

echo "🚀 Discord到微信桥接器 - 安装脚本"
echo "=================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"
echo ""

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到pip3，请先安装pip"
    exit 1
fi

# 安装依赖
echo "📦 开始安装Python依赖包..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 依赖安装完成！"
    echo ""
    echo "📝 接下来的步骤："
    echo "1. 编辑 config.py 文件，填入你的Discord频道URL和微信接收者名称"
    echo "2. 运行: python3 discord_to_wechat.py"
    echo ""
    echo "📖 详细使用说明请查看 README.md"
else
    echo ""
    echo "❌ 依赖安装失败，请检查网络连接"
    exit 1
fi

