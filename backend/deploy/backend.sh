#!/bin/bash

# 切换到当前脚本所在的目录，确保后续操作都在正确路径下执行
cd "$(dirname "$0")" || exit

# 切换到上级目录，准备执行后续操作
cd ..

# 启动 Uvicorn 服务器，监听所有网络接口的 8080 端口，并开启自动重载功能
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 --log-level trace
