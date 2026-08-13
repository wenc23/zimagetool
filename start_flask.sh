#!/bin/bash

echo "========================================"
echo "Z-Image-Turbo Flask Web UI 启动脚本"
echo "========================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python 3.10+"
    exit 1
fi

echo "✅ 检测到Python环境"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "🔧 激活虚拟环境..."
    source venv/bin/activate
else
    echo "ℹ️ 未找到虚拟环境，使用系统Python环境"
fi

# 检查依赖
echo "📦 检查依赖包..."
if ! python3 -c "import flask, torch, diffusers, transformers, accelerate, PIL, requests" &> /dev/null; then
    echo "⚠️ 依赖不完整，正在安装已锁定的依赖..."
    python3 -m pip install -r requirements.txt || exit 1
else
    echo "✅ 依赖包已安装"
fi

# 启动Flask应用
echo "🚀 启动Flask Web UI..."
echo "📱 访问地址: http://localhost:5000"
echo "⏹️ 按 Ctrl+C 停止服务"
echo "========================================"

python3 flask_app.py
