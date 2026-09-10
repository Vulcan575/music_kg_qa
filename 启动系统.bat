@echo off
chcp 65001 >nul
echo ========================================
echo 启动系统 - 后端Flask服务
echo ========================================

cd /d %~dp0
cd web_app

echo 正在安装Python依赖...
pip install -r ../requirements.txt -q

echo 正在启动Flask后端服务...
python app.py

pause
