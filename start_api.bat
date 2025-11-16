@echo off
title API Server - Port 8000
set PYTHONPATH=C:\Users\Nauti\Desktop\Cursor\src
cd /d "C:\Users\Nauti\Desktop\Cursor"
"C:\Users\Nauti\miniconda3\python.exe" -m uvicorn polylog6.api.main:app --host 127.0.0.1 --port 8000 --reload
pause
