## 目录结构

```text
backend
├── .gitignore
├── deploy
│   ├── backend.bat
│   ├── backend.sh
│   └── requirements.txt
├── docs
│   ├── README.md
│   └── imgs
│       └── docker-option.png
├── intellide
│   ├── __init__.py
│   ├── cache
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   └── startup.py
│   ├── config.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── model.py
│   │   └── startup.py
│   ├── deprecated
│   │   ├── __init__.py
│   │   ├── router
│   │   │   ├── __init__.py
│   │   │   ├── entry.py
│   │   │   └── share.py
│   │   └── tests
│   │       ├── __init__.py
│   │       ├── test_entry.py
│   │       └── test_share.py
│   ├── docker
│   │   ├── __init__.py
│   │   └── startup.py
│   ├── main.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── course_chat.py
│   │   ├── course_directory.py
│   │   ├── course_directory_entry.py
│   │   ├── course_student.py
│   │   ├── surprise.py
│   │   └── user.py
│   ├── storage
│   │   ├── __init__.py
│   │   ├── startup.py
│   │   └── storage.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── pytest.ini
│   │   ├── test_course.py
│   │   ├── test_user.py
│   │   └── utils.py
│   └── utils
│       ├── __init__.py
│       ├── auth.py
│       ├── email.py
│       ├── path.py
│       ├── response.py
│       └── websocket.py
└── tools
    └── tree.py

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

### 2. 开启Docker远程监听功能

启动Docker的`Expose daemon on tcp://localhost:2375 without TLS`选项

![docker-option](./imgs/docker-option.png)

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

**注意事项：** 若docker中没有预安装镜像，请在第一次启动后端程序时时打开梯子以拉取镜像

## 查看后端相关接口

后端启动后，可以通过以下方式查看 API 文档：

- **Swagger UI** 文档：  
  打开浏览器，访问 [http://localhost:8080/docs](http://localhost:8080/docs)

- **ReDoc** 文档：  
  打开浏览器，访问 [http://localhost:8080/redoc](http://localhost:8080/redoc)

FastAPI 采用 OpenAPI 规范自动生成 API 文档，无需额外配置。
