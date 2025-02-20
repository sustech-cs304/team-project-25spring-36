@echo off
cd /d "%~dp0"
cd ..
if not exist "storage" mkdir storage
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080