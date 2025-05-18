#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
import json

def run_command(command, cwd=None):
    """运行命令并打印输出"""
    print(f"运行命令: {' '.join(command)}")
    process = subprocess.run(command, cwd=cwd, check=False)
    return process.returncode

def ensure_poetry_installed():
    """确保已安装Poetry"""
    try:
        subprocess.run(['poetry', '--version'], check=True, stdout=subprocess.PIPE)
        print("Poetry已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("正在安装Poetry...")
        subprocess.run(['pip', 'install', 'poetry'], check=True)
        print("Poetry安装成功")

def install_dependencies():
    """安装项目依赖"""
    print("安装项目依赖...")
    return run_command(['poetry', 'install', '--no-root'])

def run_linters():
    """运行代码检查工具"""
    print("运行代码格式化和检查...")
    results = []
    
    print("运行Black格式化...")
    results.append(run_command(['poetry', 'run', 'black', 'backend']))
    
    print("运行isort导入排序...")
    results.append(run_command(['poetry', 'run', 'isort', 'backend']))
    
    print("运行flake8检查...")
    results.append(run_command(['poetry', 'run', 'flake8', 'backend']))
    
    print("运行mypy类型检查...")
    results.append(run_command(['poetry', 'run', 'mypy', 'backend']))
    
    return all(result == 0 for result in results)

def run_tests():
    """运行测试"""
    print("确保后端服务初始化...")
    # 启动后端服务进程（类似backend.bat的功能）
    import subprocess
    import time
    import signal
    import os
    
    # 从当前工作目录启动后端服务
    backend_process = subprocess.Popen(
        ['poetry', 'run', 'uvicorn', 'intellide.main:app', '--host', '0.0.0.0', '--port', '8080', '--log-level', 'trace'],
        cwd='backend'
    )
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(10)

    
    if os.name == 'nt':  # Windows
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(backend_process.pid)])
    else:  # Linux/Mac
        backend_process.send_signal(signal.SIGTERM)
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    print("初始化后端服务完成...")

    
    # 运行测试
    print("运行pytest测试...")
    result = run_command(['poetry', 'run', 'pytest', '-v', '--cov=backend','--cov-report=html', 'backend/intellide/tests'])
    
    return result
        
def generate_docs():
    """生成API文档"""
    print("生成API文档...")
    docs_dir = Path('backend/docs')
    docs_dir.mkdir(exist_ok=True, parents=True)
    
    # 这个命令会启动测试服务器，生成OpenAPI文档
    print("生成OpenAPI规范文档...")
    with open(docs_dir / 'openapi.json', 'w') as f:
        result = subprocess.run(
            ['poetry', 'run', 'python', '-c', 
             'from intellide.main import app; import json; print(json.dumps(app.openapi(), indent=2))'],
            stdout=f,
            cwd='backend',
            check=False
        )
    return result.returncode == 0

def build_package():
    """构建Python包"""
    print("构建Python包...")
    return run_command(['poetry', 'build'])

def clean_build_artifacts():
    """清理构建过程中产生的临时文件"""
    print("清理构建文件...")
    
    # 需要清理的目录和文件模式
    patterns_to_clean = [
        "dist/*",
        "build/*",
        ".coverage",
        ".pytest_cache",
        "**/__pycache__",
        "**/*.pyc",
        "backend/docs/openapi.json"
    ]
    
    import glob
    import shutil
    
    for pattern in patterns_to_clean:
        for path in glob.glob(pattern, recursive=True):
            print(f"删除: {path}")
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    print("清理完成")
    return 0

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        return clean_build_artifacts()
    
    ensure_poetry_installed()
    
    # 安装依赖
    if install_dependencies() != 0:
        print("依赖安装失败")
        return 1
    
    # 一般不进行代码检查
    # # 运行代码检查
    # if run_linters() != True:
    #     print("代码检查失败，但继续执行其他任务")
    
    # 运行测试
    if run_tests() != 0:
        print("测试失败，但继续执行其他任务")
    
    # 一般不生成文档
    # # 生成文档
    # if generate_docs() != True:
    #     print("文档生成失败，但继续执行其他任务")
    
    # 构建包
    if build_package() != 0:
        print("构建失败")
        return 1
    
    print("构建完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 