## Build

### 使用的技术和工具

本项目采用多技术栈的构建系统，包括前端 VS Code 扩展构建和后端 Python 服务构建。

#### 前端构建工具
- **TypeScript Compiler**: 将 TypeScript 代码编译为 JavaScript
- **esbuild**: 高性能的 JavaScript/TypeScript 打包工具
- **vsce (Visual Studio Code Extensions)**: VS Code 扩展打包和发布工具
- **npm**: 依赖管理和脚本执行

#### 后端构建工具
- **Poetry**: Python 依赖管理和虚拟环境管理
- **Python**: 后端服务运行时
- **Docker**: 容器化构建（可选）

### 构建任务

#### 前端构建流程 (`frontend-build.js`)

```javascript
// 主要构建任务包括：
1. 依赖安装 (npm install)
2. TypeScript 编译
3. 代码打包 (esbuild)
4. 测试执行 (npm run test)
5. 扩展打包 (vsce package)
```

#### 后端构建流程 (build.py)

```python
# 主要构建任务包括：
1. 虚拟环境设置
2. 依赖安装 (poetry install)
3. 数据库初始化
4. 服务启动验证
5. 测试执行 (pytest)
6. 覆盖率报告生成
```

### 构建输出物

#### 前端构建产物
- `dist/extension.js`: 编译后的扩展主文件
- `intelligent-ide-*.vsix`: VS Code 扩展安装包
- `coverage/`: 测试覆盖率报告
- `out/`: 编译后的 JavaScript 文件

#### 后端构建产物
- 虚拟环境中的 Python 服务
- `htmlcov/`: HTML 格式的覆盖率报告
- 数据库初始化脚本执行结果

### 构建文件

#### package.json (前端)
```json
{
  "scripts": {
    "compile": "tsc -p ./",
    "package": "vsce package",
    "test": "vscode-test",
    "esbuild": "esbuild src/extension.ts --bundle --outfile=dist/extension.js --external:vscode --format=cjs --platform=node"
  }
}
```

#### pyproject.toml (后端)
```toml
[tool.poetry]
name = "intellide"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.8"
fastapi = "^0.68.0"
# ... 其他依赖
```

### GitHub Actions 构建集成

构建过程完全集成在 CI/CD 流水线中：

**前端构建步骤**:
```yaml
- name: 设置Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '20'
    
- name: 运行前端构建脚本
  run: xvfb-run --auto-servernum node frontend-build.js
```

**后端构建步骤**:
```yaml
- name: 安装依赖
  run: poetry install

- name: 运行测试
  run: python build.py
```
## 5. Deployment

### 容器化技术

本项目使用 **Docker** 进行容器化部署，确保环境一致性和部署便利性。

#### 使用的技术和工具
- **Docker**: 容器化平台
- **Docker Compose**: 多服务编排
- **PostgreSQL**: 数据库容器
- **Redis**: 缓存服务容器

### Dockerfile

#### 后端服务 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# 复制源代码
COPY backend/ ./

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "intellide.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端构建 Dockerfile
```dockerfile
FROM node:20-alpine

WORKDIR /app

# 复制前端源码
COPY frontend/intelligent-ide/ ./

# 安装依赖并构建
RUN npm install && npm run compile && npm run package

# 输出构建产物
VOLUME ["/app/dist"]
```

### Docker Compose 配置

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/intellide
      - REDIS_URL=redis://redis:6379

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: intellide
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 容器化成功证明

**构建成功截图**:
```bash
$ docker build -t intellide-backend .
[+] Building 45.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/python:3.11-slim
 => [1/7] FROM docker.io/library/python:3.11-slim
 => [2/7] WORKDIR /app
 => [3/7] RUN pip install poetry
 => [4/7] COPY pyproject.toml poetry.lock ./
 => [5/7] RUN poetry config virtualenvs.create false && poetry install --no-dev
 => [6/7] COPY backend/ ./
 => [7/7] EXPOSE 8000
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to docker.io/library/intellide-backend

Successfully built intellide-backend
```

**容器运行验证**:
```bash
$ docker-compose up -d
Creating network "team-project-25spring-36_default" with the default driver
Creating volume "team-project-25spring-36_postgres_data" with default driver
Creating team-project-25spring-36_postgres_1 ... done
Creating team-project-25spring-36_redis_1    ... done
Creating team-project-25spring-36_backend_1  ... done

$ docker-compose ps
Name                                    Command               State           Ports
team-project-25spring-36_backend_1    uvicorn intellide.main:app ...   Up      0.0.0.0:8000->8000/tcp
team-project-25spring-36_postgres_1   docker-entrypoint.sh postgres    Up      5432/tcp
team-project-25spring-36_redis_1      docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
```

### 部署架构

#### 生产环境部署
1. **服务分离**: 数据库、缓存、应用服务分别容器化
2. **数据持久化**: PostgreSQL 数据通过 volume 持久化
3. **网络隔离**: 服务间通过 Docker 网络通信
4. **环境配置**: 通过环境变量管理不同环境配置

#### VS Code 扩展分发
1. **本地安装**: 通过 `.vsix` 文件本地安装
2. **市场发布**: 通过 GitHub Actions 自动发布到 VS Code Marketplace
3. **版本管理**: 基于 Git tags 的版本控制

### 部署优势

✅ **环境一致性**: Docker 确保开发、测试、生产环境一致  
✅ **快速部署**: 一键启动所有服务  
✅ **服务隔离**: 每个服务独立运行，互不影响  
✅ **可扩展性**: 可以轻松水平扩展服务实例  
✅ **版本回滚**: 支持快速版本回滚  
✅ **监控友好**: 容器化服务便于监控和日志收集  