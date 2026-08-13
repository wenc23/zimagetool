@echo off
chcp 65001 >nul
echo ====================================
echo    Z-Image-Turbo Flask Web UI
echo ====================================
echo.
echo 正在启动 Flask 服务器...
echo.

if not exist "venv\Scripts\python.exe" (
    echo ❌ 未找到虚拟环境，请先使用 Python 3.10+ 执行: python -m venv venv
    pause
    exit /b 1
)

"venv\Scripts\python.exe" --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 虚拟环境已失效（通常是基础 Python 被移动或卸载）
    echo 请删除或重命名旧 venv，然后使用 Python 3.10+ 重新创建并安装 requirements.txt
    pause
    exit /b 1
)

"venv\Scripts\python.exe" -c "import flask, torch, diffusers, transformers, accelerate, PIL, requests" >nul 2>&1
if errorlevel 1 (
    echo ❌ 依赖不完整，请执行: venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

"venv\Scripts\python.exe" flask_app.py

pause 
