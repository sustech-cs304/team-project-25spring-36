@echo off
:: 切换到当前脚本所在的目录
cd /d "%~dp0"

:: 返回上一层目录，准备执行后续操作
cd ..

:: 检查是否存在名为 "storage" 的目录，如果不存在则创建
if not exist "storage" mkdir storage

:: 启动 Uvicorn 服务器，监听所有网络接口的 8080 端口，并开启自动重载功能
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080
