@echo off
setlocal
cd /d "%~dp0"

start "A-Mart Admin Server" powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-admin.ps1"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:9000/admin/"
start "" "http://127.0.0.1:9000/"
