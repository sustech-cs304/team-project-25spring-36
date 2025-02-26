## 目录结构
```text
└── backend
    ├── app
    │  ├── __init__.py
    │  ├── config.py
    │  ├── main.py
    │  ├── database
    │  │  ├── __init__.py
    │  │  ├── engine.py
    │  │  └── model.py
    │  ├── router
    │  │  ├── __init__.py
    │  │  ├── entry.py
    │  │  ├── share.py
    │  │  └── user.py
    │  └── util
    │      ├── __init__.py
    │      ├── encrypt.py
    │      ├── path.py
    │      └── response.py
    ├── deploy
    │  ├── backend.bat
    │  ├── backend.sh
    │  ├── docker-compose.yaml
    │  └── requirements.txt
    ├── docs
    │  └── README.md
    ├── storage
    └── tests
```
## 启动后端服务

### 1. 安装依赖

#### 在本机安装 Python
[下载并安装 Python](https://www.python.org/downloads/)（推荐 3.11 及以上版本）。

#### 在本机安装 Docker
[下载并安装 Docker](https://www.docker.com/) 以运行必要的依赖服务。

#### 安装 Python 依赖

进入 `deploy` 目录并安装所需的 Python 包：

```sh
cd deploy
pip install -r requirements.txt
```

### 2. 启动依赖服务

在 `deploy` 目录下运行以下命令以启动数据库等服务：

```sh
cd deploy
docker-compose up -d
```

### 3. 启动后端服务器

在 `deploy` 目录下运行以下命令以启动后端服务：

#### Windows 平台

```sh
cd deploy
backend.bat
```

#### Linux/Mac 平台

```sh
cd deploy
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
