@echo off
chcp 65001 >nul
title Z-Image-Turbo Web UI 启动器

echo ========================================
echo 🎨 Z-Image-Turbo Web UI 启动器
echo ========================================
echo.

echo 📦 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请确保已安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境正常

echo 📦 检查虚拟环境...
if exist "venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️ 未找到虚拟环境，使用系统Python
)

echo 📦 检查依赖...
pip list | findstr "gradio" >nul
if errorlevel 1 (
    echo 🔧 安装Gradio依赖...
    pip install gradio
)

echo.
echo 🚀 启动Web UI...
echo 📱 访问地址: http://localhost:7860
echo ⏹️ 按 Ctrl+C 停止服务
echo.

python webui.py

pause