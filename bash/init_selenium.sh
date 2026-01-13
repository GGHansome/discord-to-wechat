#!/bin/bash

echo "🔧 初始化Selenium数据目录..."
echo "=================================="
echo ""

# 创建selenium_data目录
if [ ! -d "./selenium_data" ]; then
    echo "📁 创建selenium_data目录..."
    mkdir -p ./selenium_data
    
    if [ $? -eq 0 ]; then
        echo "✅ selenium_data目录创建成功"
    else
        echo "❌ selenium_data目录创建失败"
        exit 1
    fi
else
    echo "ℹ️  selenium_data目录已存在"
fi

# 设置目录权限为777
echo "🔓 设置目录权限为777..."
chmod 777 ./selenium_data

if [ $? -eq 0 ]; then
    # 清理可能残留的 Chrome 锁文件（跨系统/异常退出时常见），避免 selenium 中 Chrome 启动失败
    rm -f ./selenium_data/SingletonCookie ./selenium_data/SingletonLock ./selenium_data/SingletonSocket 2>/dev/null || true
    echo "✅ 权限设置成功"
    echo ""
    echo "📋 目录信息："
    ls -ld ./selenium_data
    echo ""
    echo "✅ 初始化完成！"
else
    echo "❌ 权限设置失败"
    exit 1
fi

