# 使用Poetry进行测试和构建

## 项目自动化测试与构建说明

本项目使用Poetry进行依赖管理、测试和构建。Poetry提供了一个简单而强大的方式来管理Python项目的依赖、环境和构建流程。

## 安装Poetry

如果您尚未安装Poetry，可以通过以下命令安装：

### Windows:
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Linux/MacOS:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

安装后，确保将Poetry添加到您的PATH环境变量中。

## 使用自动构建脚本

我们提供了一个自动化构建脚本，可以执行所有测试和构建步骤：

```bash
python build.py
```

该脚本会执行以下任务：
1. 确保Poetry已安装
2. 安装项目依赖
3. 运行代码检查工具（格式化和静态分析）（可选）
4. 运行自动化测试（包括后端服务初始化和关闭）
5. 生成API文档（可选）
6. 构建Python包

## 手动执行构建和测试步骤

### 1. 安装依赖

```bash
poetry install
```

### 2. 运行代码质量检查(可选)

格式化代码：
```bash
poetry run black backend
poetry run isort backend
```

静态分析：
```bash
poetry run flake8 backend
poetry run mypy backend
```

### 3. 运行测试

测试前必须先初始化后端服务环境（已在build.py中自动处理）。如果手动测试，需要按以下步骤进行：

1. 首先启动后端服务：
```bash
# 在backend目录下执行
cd backend
poetry run uvicorn intellide.main:app --host 0.0.0.0 --port 8080 --log-level trace
```
2. 关闭后端服务：
    
    按CTRL+C或其他方式关闭


3. 执行测试：
```bash
poetry run pytest -v backend/intellide/tests
```

使用自动构建脚本时，这一过程会自动处理，无需手动启动服务。

带覆盖率报告的测试：
```bash
poetry run pytest -v --cov=backend backend/intellide/tests
```

生成HTML覆盖率报告（默认在build.py中使用此模式）：
```bash
poetry run pytest -v --cov=backend --cov-report=html backend/intellide/tests
```

### 4. 构建项目

```bash
poetry build
```

构建完成后，生成的包将位于`dist/`目录下。

## 测试框架说明

本项目使用Pytest作为测试框架。测试文件位于`backend/intellide/tests/`目录下，主要包括：

- `test_course.py`: 课程相关功能测试
- `test_user.py`: 用户管理相关功能测试
- `conftest.py`: 测试固件和工具函数
- `utils.py`: 测试辅助函数

前端部分使用VSCode的测试框架，测试文件位于`frontend/intelligent-ide/src/test/`目录下。

## 测试覆盖率

测试覆盖了项目的核心功能，包括但不限于：

1. 用户注册、登录和权限验证
2. 课程创建、更新和删除
3. 文件存储和访问
4. API接口功能和错误处理

使用覆盖率报告可以查看具体的测试覆盖情况：

```bash
poetry run pytest --cov=backend --cov-report=term backend/intellide/tests
```

## 构建产物

成功构建后，将生成以下产物：

1. Python包（wheel和tar.gz格式）位于`dist/`目录
2. HTML测试覆盖率报告位于`htmlcov/`目录
3. API文档位于`backend/docs/`目录（如果选择生成） 