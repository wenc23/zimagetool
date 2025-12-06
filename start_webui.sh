#!/bin/bash

echo "========================================"
echo "🎨 Z-Image-Turbo Web UI 启动器"
echo "========================================"
echo

echo "📦 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请确保已安装Python 3.8+"
    exit 1
fi

echo "✅ Python环境正常"

echo "📦 检查虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    echo "🔧 激活虚拟环境..."
    source venv/bin/activate
else
    echo "⚠️ 未找到虚拟环境，使用系统Python"
fi

echo "📦 检查依赖..."
if ! pip list | grep -q gradio; then
    echo "🔧 安装Gradio依赖..."
    pip install gradio
fi

echo
echo "🚀 启动Web UI..."
echo "📱 访问地址: http://localhost:7860"
echo "⏹️ 按 Ctrl+C 停止服务"
echo

python3 webui.py
