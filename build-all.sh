#!/bin/bash


echo -e "===================================="
echo -e "  智能IDE项目自动化构建与测试脚本  "
echo -e "===================================="

# 检查操作系统类型
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo -e "检测到Windows操作系统"
    IS_WINDOWS=true
else
    echo -e "检测到UNIX操作系统"
    IS_WINDOWS=false
fi

# 后端构建与测试
echo -e "\n开始后端构建与测试..."
if [ "$IS_WINDOWS" = true ]; then
    python build.py
else
    python3 build.py
fi

if [ $? -ne 0 ]; then
    echo -e "后端构建或测试失败，请查看上面的错误信息"
else
    echo -e "后端构建与测试完成"
fi

# 前端构建与测试
echo -e "\n开始前端构建与测试..."
if [ "$IS_WINDOWS" = true ]; then
    node frontend-build.js
else
    node frontend-build.js
fi

if [ $? -ne 0 ]; then
    echo -e "前端构建或测试失败，请查看上面的错误信息"
else
    echo -e "前端构建与测试完成"
fi

echo -e "\n===================================="
echo -e "构建与测试流程完成!"
echo -e "===================================="
echo -e "后端测试报告可在: htmlcov/ 目录查看"
echo -e "前端测试报告可在: frontend/intelligent-ide/coverage/ 目录查看"
echo -e "构建产物: dist/ 和 frontend/intelligent-ide/out/ 目录" 