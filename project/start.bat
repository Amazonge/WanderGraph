@echo off
chcp 65001 >nul
echo ========================================
echo   WanderGraph 一键启动
echo ========================================
echo.

cd /d %~dp0
python start.py
pause
