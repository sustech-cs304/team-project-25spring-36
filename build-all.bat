@echo off
chcp 65001 > nul
echo ====================================
echo   智能IDE项目自动化构建与测试脚本
echo ====================================


echo 开始后端构建与测试...
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo 后端构建或测试失败，请查看上面的错误信息
) else (
    echo 后端构建与测试完成
)

echo.
echo 开始前端构建与测试...
node frontend-build.js
if %ERRORLEVEL% NEQ 0 (
    echo 前端构建或测试失败，请查看上面的错误信息
) else (
    echo 前端构建与测试完成
)

echo.
echo ====================================
echo 构建与测试流程完成!
echo ====================================
echo 后端测试报告可在: htmlcov/ 目录查看
echo 前端测试报告可在: frontend/intelligent-ide/coverage/ 目录查看
echo 构建产物: dist/ 和 frontend/intelligent-ide/out/ 目录

pause 