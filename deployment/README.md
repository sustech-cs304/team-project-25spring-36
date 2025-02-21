## 目录结构

```
team-project-25spring-36/
├── backend/
│   ├── db/
│   │   ├── engine.py
│   │   ├── model.py
│   ├── router/
│   │   ├── user.py
│   │   ├── entry.py
│   │   ├── share.py
│   ├── util/
│   │   ├── auth.py
│   │   ├── response.py
│   │   ├── encrypt.py
│   │   ├── path.py
│   ├── main.py
├── deployment/
│   ├── backend.bat
│   ├── backend.sh
│   ├── docker-compose.yaml
│   ├── requirements.txt
│   ├── README.md
```

## 启动后端服务

### 1. 安装依赖

#### 在本机安装 Python
[下载并安装 Python](https://www.python.org/downloads/)（推荐 3.11 及以上版本）。

#### 在本机安装 Docker
[下载并安装 Docker](https://www.docker.com/) 以运行必要的依赖服务。

#### 安装 Python 依赖

进入 `deployment` 目录并安装所需的 Python 包：

```sh
cd deployment
pip install -r requirements.txt
```

### 2. 启动依赖服务

在 `deployment` 目录下运行以下命令以启动数据库等服务：

```sh
cd deployment
docker-compose up -d
```

### 3. 启动后端服务器

在 `deployment` 目录下运行以下命令以启动后端服务：

#### Windows 平台

```sh
cd deployment
backend.bat
```

#### Linux/Mac 平台

```sh
cd deployment
sh backend.sh
```

该脚本将启动 FastAPI 服务器。

## 查看后端相关接口

后端启动后，可以通过以下方式查看 API 文档：

- **Swagger UI** 文档：  
  打开浏览器，访问 [http://localhost:8080/docs](http://localhost:8080/docs)
  
- **ReDoc** 文档：  
  打开浏览器，访问 [http://localhost:8080/redoc](http://localhost:8080/redoc)

FastAPI 采用 OpenAPI 规范自动生成 API 文档，无需额外配置。
