@echo off
chcp 65001 >nul
echo ====================================
echo    Z-Image-Turbo Flask Web UI
echo ====================================
echo.
echo 正在启动 Flask 服务器...
echo.

REM 激活虚拟环境并运行
call venv\Scripts\activate.bat
python flask_app.py
deactivate

pause 
