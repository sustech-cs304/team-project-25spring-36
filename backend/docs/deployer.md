# 后端开发者文档

## 目录

1. [系统概述](#1-系统概述)
2. [环境准备](#2-环境准备)
   - [2.1 必要软件](#21-必要软件)
   - [2.2 安装Python依赖](#22-安装python依赖)
   - [2.3 配置Docker](#23-配置docker)
3. [服务启动](#3-服务启动)
   - [3.1 Windows平台](#31-windows平台)
   - [3.2 Linux/Mac平台](#32-linuxmac平台)
   - [3.3 验证服务](#33-验证服务)
4. [系统架构](#4-系统架构)
   - [4.1 目录结构](#41-目录结构)
   - [4.2 核心组件](#42-核心组件)
   - [4.3 数据模型](#43-数据模型)
5. [API接口说明](#5-api接口说明)
   - [5.1 用户管理](#51-用户管理)
   - [5.2 课程管理](#52-课程管理)
   - [5.3 课程目录管理](#53-课程目录管理)
   - [5.4 课程文件管理](#54-课程文件管理)
   - [5.5 协作功能](#55-协作功能)
   - [5.6 作业管理](#56-作业管理)
   - [5.7 聊天功能](#57-聊天功能)
6. [认证机制](#6-认证机制)
   - [6.1 身份验证流程](#61-身份验证流程)
   - [6.2 JWT令牌管理](#62-jwt令牌管理)
7. [配置说明](#7-配置说明)
   - [7.1 服务器配置](#71-服务器配置)
   - [7.2 数据库配置](#72-数据库配置)
   - [7.3 缓存配置](#73-缓存配置)
   - [7.4 Docker配置](#74-docker配置)
   - [7.5 邮件配置](#75-邮件配置)
8. [常见问题与解决方案](#8-常见问题与解决方案)
9. [开发者指南](#9-开发者指南)
   - [9.1 添加新接口](#91-添加新接口)
   - [9.2 数据库迁移](#92-数据库迁移)

## 1. 系统概述

本系统是一个基于FastAPI开发的教育管理后端服务，提供了完整的课程管理、用户管理、文件管理、协作编辑、作业管理等功能。系统采用了现代化的Web开发技术栈，包括:

- **FastAPI**: 高性能的Python Web框架
- **PostgreSQL**: 强大的关系型数据库
- **Redis**: 高性能缓存服务
- **Docker**: 容器化部署
- **JWT**: 安全的用户认证机制

系统主要面向教育领域，支持教师创建课程、管理课程内容、布置作业，学生可以加入课程、参与协作编辑、提交作业等。

## 2. 环境准备

### 2.1 必要软件

开始使用前，请确保已安装以下软件:

- **Python 3.11+**: [下载地址](https://www.python.org/downloads/)
  - 确保安装时勾选"Add Python to PATH"选项
  - 验证安装: 打开命令行，输入`python --version`，确认输出版本号

- **Docker**: [下载地址](https://www.docker.com/products/docker-desktop/)
  - 安装完成后启动Docker Desktop
  - 验证安装: 打开命令行，输入`docker --version`，确认输出版本号

### 2.2 安装Python依赖

系统依赖于多个Python包，请按照以下步骤安装:

1. 打开命令行终端
2. 进入项目的`deploy`目录:
   ```sh
   cd path/to/project/backend/deploy
   ```
3. 安装依赖包:
   ```sh
   pip install -r requirements.txt
   ```

安装过程中如遇到问题，可能需要安装额外的系统依赖或升级pip:
```sh
pip install --upgrade pip
```

### 2.3 配置Docker

系统需要Docker提供数据库和缓存服务，请按照以下步骤配置:

1. 打开Docker Desktop
2. 进入设置 (Settings)
3. 选择"Docker Engine"选项
4. 启用"Expose daemon on tcp://localhost:2375 without TLS"选项:
   ![docker-option](./backend/docs/imgs/docker-option.png)
5. 点击"Apply & Restart"应用更改

> **注意**: 出于安全考虑，此配置仅适用于开发环境。在生产环境中，应使用更安全的配置方式。

## 3. 服务启动

### 3.1 Windows平台

在Windows系统中启动后端服务:

1. 打开命令行终端
2. 进入`deploy`目录:
   ```sh
   cd path/to/project/backend/deploy
   ```
3. 执行启动脚本:
   ```sh
   backend.bat
   ```

### 3.2 Linux/Mac平台

在Linux或Mac系统中启动后端服务:

1. 打开终端
2. 进入`deploy`目录:
   ```sh
   cd path/to/project/backend/deploy
   ```
3. 执行启动脚本:
   ```sh
   sh backend.sh
   ```

### 3.3 验证服务

服务启动后，可通过以下方式验证:

- **API文档访问**: 
  - Swagger UI: http://localhost:8080/docs
  - ReDoc: http://localhost:8080/redoc

- **直接API测试**:
  - 可以使用Swagger UI直接在浏览器中测试API
  - 也可以使用Postman或curl等工具测试

> **注意**: 首次启动时，系统会自动拉取必要的Docker镜像。如果您所在的网络环境受限，可能需要使用代理。

## 4. 系统架构

### 4.1 目录结构

```text
backend
├── .gitignore # Git忽略文件
├── deploy/ # 部署脚本和依赖
│ ├── backend.bat # Windows启动脚本
│ ├── backend.sh # Linux/Mac启动脚本
│ └── requirements.txt # Python依赖列表
├── docs/ # 文档
│ ├── README.md # 基本使用文档
│ └── imgs/ # 文档图片
├── intellide/ # 主应用代码
│ ├── init.py
│ ├── cache/ # 缓存相关代码
│ │ ├── init.py
│ │ ├── cache.py # 缓存实现
│ │ └── startup.py # 缓存启动配置
│ ├── config.py # 系统配置
│ ├── database/ # 数据库相关代码
│ │ ├── init.py
│ │ ├── database.py # 数据库连接
│ │ ├── model.py # 数据模型定义
│ │ └── startup.py # 数据库启动配置
│ ├── docker/ # Docker相关代码
│ │ ├── init.py
│ │ └── startup.py # Docker启动配置
│ ├── main.py # 应用入口
│ ├── routers/ # API路由
│ │ ├── init.py
│ │ ├── course.py # 课程相关API
│ │ ├── course_chat.py # 课程聊天API
│ │ ├── course_directory.py # 课程目录API
│ │ ├── ...
│ │ └── user.py # 用户管理API
│ ├── storage/ # 存储相关代码
│ │ ├── init.py
│ │ ├── startup.py # 存储启动配置
│ │ └── storage.py # 存储实现
│ └── utils/ # 工具函数
│ ├── init.py
│ ├── auth.py # 认证相关
│ ├── email.py # 邮件相关
│ ├── ...
└── tools/ # 辅助工具
└── tree.py # 目录结构生成工具
```

### 4.2 核心组件

系统由以下核心组件组成:

1. **FastAPI应用**: 提供HTTP和WebSocket接口，处理请求和响应
2. **路由模块**: 定义API端点和业务逻辑
3. **数据库模块**: 管理与PostgreSQL数据库的连接和交互
4. **缓存模块**: 使用Redis提供高速缓存服务
5. **Docker模块**: 管理Docker容器，提供数据库和缓存服务
6. **存储模块**: 管理文件存储
7. **工具模块**: 提供认证、邮件等通用功能

### 4.3 数据模型

系统主要包含以下数据模型:

- **User**: 用户信息，包括教师和学生
- **Course**: 课程信息
- **CourseStudent**: 学生选课关系
- **CourseDirectory**: 课程目录
- **CourseDirectoryEntry**: 课程文件和子目录
- **CourseCollaborativeDirectoryEntry**: 课程协作文件
- **CourseHomeworkAssignment**: 作业布置
- **CourseHomeworkSubmission**: 作业提交

## 5. API接口说明

系统提供了丰富的API接口，所有接口都遵循RESTful风格，使用JSON格式进行数据交换。

### 5.1 用户管理

#### 获取注册验证码

- **路径**: `/api/user/register/code`
- **方法**: GET
- **参数**: 
  - `email`: 用户邮箱
- **响应**: 
  - 成功: `{"status": "success"}`
  - 失败: `{"status": "error", "message": "错误信息"}`
- **说明**: 系统会向指定邮箱发送6位验证码，有效期5分钟

#### 用户注册

- **路径**: `/api/user/register`
- **方法**: POST
- **参数**: 
  ```json
  {
    "username": "用户名",
    "password": "密码",
    "email": "邮箱",
    "code": "验证码"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "user_id": 用户ID,
      "token": "认证令牌"
    }
  }
  ```
- **说明**: 注册成功后直接返回登录令牌，有效期24小时

#### 用户登录

- **路径**: `/api/user/login`
- **方法**: POST
- **参数**: 
  ```json
  {
    "email": "邮箱",
    "password": "密码"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "user_id": 用户ID,
      "token": "认证令牌"
    }
  }
  ```
- **说明**: 登录令牌有效期24小时

#### 获取用户信息

- **路径**: `/api/user`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "id": "用户ID",
      "username": "用户名",
      "email": "邮箱",
      "created_at": "创建时间",
      "updated_at": "更新时间",
      "uid": "用户唯一标识"
    }
  }
  ```

#### 更新用户信息

- **路径**: `/api/user`
- **方法**: PUT
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "username": "新用户名",
    "password": "新密码"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "user_id": 用户ID,
      "token": "更新后的认证令牌"
    }
  }
  ```
- **说明**: 用户名和密码字段为可选，可以只更新其中一个

### 5.2 课程管理

#### 获取课程列表

- **路径**: `/api/course`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `role`: 角色，取值为`teacher`或`student`
- **响应**: 
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "课程ID",
        "teacher_id": "教师ID",
        "name": "课程名称",
        "description": "课程描述",
        "created_at": "创建时间",
        "updated_at": "更新时间"
      },
      ...
    ]
  }
  ```
- **说明**: 
  - 教师: 返回创建的所有课程
  - 学生: 返回加入的所有课程

#### 创建课程

- **路径**: `/api/course`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "name": "课程名称",
    "description": "课程描述"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "course_id": 课程ID
    }
  }
  ```
- **说明**: 只有教师才能创建课程

#### 删除课程

- **路径**: `/api/course`
- **方法**: DELETE
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `course_id`: 课程ID
- **响应**: 
  ```json
  {
    "status": "success"
  }
  ```
- **说明**: 只有课程创建者才能删除课程

### 5.3 课程目录管理

系统支持创建和管理课程目录，用于组织课程文件。

#### 创建课程目录

- **路径**: `/api/course/directory`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "course_id": 课程ID,
    "name": "目录名称",
    "permission": {
      "/": ["read", "write", "upload", "delete"]
    }
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "directory_id": 目录ID
    }
  }
  ```
- **说明**: 
  - 权限配置是针对目录路径的，`/`表示根路径
  - 可配置的权限包括: `read`, `write`, `upload`, `delete`

#### 获取课程目录列表

- **路径**: `/api/course/directory`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `course_id`: 课程ID
- **响应**: 
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "目录ID",
        "course_id": "课程ID",
        "name": "目录名称",
        "permission": {
          "/": ["read", "write", "upload", "delete"]
        },
        "created_at": "创建时间",
        "updated_at": "更新时间"
      },
      ...
    ]
  }
  ```

### 5.4 课程文件管理

系统支持在课程目录中上传、下载、管理文件。

#### 上传文件

- **路径**: `/api/course/directory/entry/upload`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **表单参数**: 
  - `course_directory_id`: 目录ID
  - `path`: 文件路径
  - `file`: 文件内容
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "entry_id": 文件ID
    }
  }
  ```
- **说明**: 路径格式为`/folder/subfolder/file.txt`

#### 下载文件

- **路径**: `/api/course/directory/entry/download`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `course_directory_entry_id`: 文件ID
- **响应**: 文件内容 (二进制流)

#### 列出目录内容

- **路径**: `/api/course/directory/entry`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `course_directory_id`: 目录ID
  - `path`: 路径 (可选，默认为根路径)
- **响应**: 
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "条目ID",
        "course_directory_id": "目录ID",
        "author_id": "创建者ID",
        "path": "路径",
        "depth": 深度,
        "type": "file或directory",
        "storage_name": "存储名称",
        "created_at": "创建时间",
        "updated_at": "更新时间"
      },
      ...
    ]
  }
  ```

### 5.5 协作功能

系统支持多用户实时协作编辑文件。

#### 创建协作文件

- **路径**: `/api/course/collaborative/directory/entry`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "course_id": 课程ID,
    "name": "文件名"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "entry_id": 文件ID
    }
  }
  ```

#### 加入协作编辑

- **路径**: `/ws/course/collaborative/directory/entry`
- **类型**: WebSocket
- **参数**: 
  - `token`: 认证令牌
  - `entry_id`: 文件ID
- **消息格式**: JSON字符串
  ```json
  {
    "type": "操作类型",
    "data": {
      // 操作数据
    }
  }
  ```

### 5.6 作业管理

系统支持教师布置作业、学生提交作业和教师评分。

#### 布置作业

- **路径**: `/api/course/homework/assignment`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "course_id": 课程ID,
    "title": "作业标题",
    "description": "作业描述",
    "deadline": "截止日期",
    "course_directory_entry_ids": [文件ID列表]
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "assignment_id": 作业ID
    }
  }
  ```

#### 获取作业列表

- **路径**: `/api/course/homework/assignment`
- **方法**: GET
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  - `course_id`: 课程ID
- **响应**: 
  ```json
  {
    "status": "success",
    "data": [
      {
        "id": "作业ID",
        "course_id": "课程ID",
        "title": "作业标题",
        "description": "作业描述",
        "deadline": "截止日期",
        "course_directory_entry_ids": [文件ID列表],
        "created_at": "创建时间",
        "updated_at": "更新时间"
      },
      ...
    ]
  }
  ```

#### 提交作业

- **路径**: `/api/course/homework/submission`
- **方法**: POST
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "homework_assignments_id": 作业ID,
    "title": "提交标题",
    "description": "提交描述",
    "course_directory_entry_ids": [文件ID列表]
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success",
    "data": {
      "submission_id": 提交ID
    }
  }
  ```

#### 评分

- **路径**: `/api/course/homework/submission/grade`
- **方法**: PUT
- **请求头**: `Access-Token: 认证令牌`
- **参数**: 
  ```json
  {
    "submission_id": 提交ID,
    "grade": 分数,
    "feedback": "反馈"
  }
  ```
- **响应**: 
  ```json
  {
    "status": "success"
  }
  ```

### 5.7 聊天功能

系统支持课程内的实时聊天功能。

#### 发起聊天

- **路径**: `/ws/course/chat`
- **类型**: WebSocket
- **参数**: 
  - `token`: 认证令牌
  - `course_id`: 课程ID
- **消息格式**: JSON字符串
  ```json
  {
    "type": "message",
    "data": {
      "content": "消息内容"
    }
  }
  ```

## 6. 认证机制

### 6.1 身份验证流程

系统使用基于JWE (JSON Web Encryption) 的认证机制，流程如下:

1. 用户通过登录或注册获取认证令牌
2. 用户在后续请求中通过`Access-Token`请求头携带令牌
3. 服务器验证令牌的有效性和过期时间
4. 验证通过后，服务器从令牌中提取用户信息并处理请求

### 6.2 JWT令牌管理

- **令牌生成**: 用户登录或注册成功后，系统生成包含用户ID和用户名的JWE令牌
- **令牌验证**: 系统在每个需要认证的API请求中验证令牌的有效性
- **令牌过期**: 令牌默认有效期为24小时，过期后需要重新登录
- **令牌刷新**: 更新用户信息后，系统会生成新的令牌

## 7. 配置说明

系统的主要配置项位于`config.py`文件中。

### 7.1 服务器配置

```python
# 服务器配置
SERVER_HOST = "0.0.0.0"  # 服务监听地址
SERVER_PORT = 8080        # 服务监听端口
```

- `SERVER_HOST`: 服务器监听地址，默认为`0.0.0.0`(所有网络接口)
- `SERVER_PORT`: 服务器监听端口，默认为`8080`

### 7.2 数据库配置

```python
# 数据库配置
DATABASE_ENGINE = "postgresql"  # 数据库引擎
DATABASE_DRIVER = "asyncpg"     # 数据库驱动
DATABASE_USER = "postgres"      # 数据库用户名
DATABASE_PASSWORD = "123456"    # 数据库密码
DATABASE_HOST = "localhost"     # 数据库主机
DATABASE_PORT = "5432"          # 数据库端口
DATABASE_NAME = "ide"           # 数据库名称
```

- `DATABASE_ENGINE`: 数据库引擎，当前仅支持`postgresql`
- `DATABASE_USER`: 数据库用户名
- `DATABASE_PASSWORD`: 数据库密码
- `DATABASE_HOST`: 数据库主机地址
- `DATABASE_PORT`: 数据库端口
- `DATABASE_NAME`: 数据库名称

### 7.3 缓存配置

```python
# 缓存配置
CACHE_ENGINE = "redis"       # 缓存引擎
CACHE_USER = ""              # 缓存用户名
CACHE_PASSWORD = "123456"    # 缓存密码
CACHE_HOST = "localhost"     # 缓存主机
CACHE_PORT = "6379"          # 缓存端口
```

- `CACHE_ENGINE`: 缓存引擎，当前仅支持`redis`
- `CACHE_PASSWORD`: Redis密码
- `CACHE_HOST`: Redis主机地址
- `CACHE_PORT`: Redis端口

### 7.4 Docker配置

```python
# docker配置
DOCKER_HOST = "localhost"    # Docker主机
DOCKER_PORT = "2375"         # Docker端口
DOCKER_URL = f"tcp://{DOCKER_HOST}:{DOCKER_PORT}"
DOCKER_CONTAINER_POSTGRESQL_NAME = "software-engineering-project-postgres"
DOCKER_CONTAINER_REDIS_NAME = "software-engineering-project-redis"
DOCKER_ENABLE = True         # 是否启用Docker
```

- `DOCKER_HOST`: Docker主机地址
- `DOCKER_PORT`: Docker API端口
- `DOCKER_ENABLE`: 是否启用Docker自动管理功能
- `DOCKER_CONTAINER_POSTGRESQL_NAME`: PostgreSQL容器名称
- `DOCKER_CONTAINER_REDIS_NAME`: Redis容器名称

### 7.5 邮件配置

```python
# 邮箱配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "example@qq.com"
SMTP_PASSWORD = "your_password"
```

- `SMTP_SERVER`: SMTP服务器地址
- `SMTP_PORT`: SMTP服务器端口
- `SMTP_USER`: 邮箱用户名
- `SMTP_PASSWORD`: 邮箱密码或授权码

## 8. 常见问题与解决方案

### 问题: 服务无法启动

可能的原因:
- Python版本不兼容
- 依赖包安装失败
- 端口被占用
- Docker服务未运行

解决方案:
- 确认Python版本为3.11+
- 重新安装依赖: `pip install -r requirements.txt`
- 更改端口配置: 修改`config.py`中的`SERVER_PORT`
- 启动Docker服务: 确保Docker Desktop正在运行

### 问题: 数据库连接失败

可能的原因:
- Docker服务未运行
- 数据库容器未启动
- 数据库配置错误

解决方案:
- 启动Docker服务
- 手动启动PostgreSQL容器: 
  ```sh
  docker run -d --name software-engineering-project-postgres -p 5432:5432 -e POSTGRES_PASSWORD=123456 postgres
  ```
- 检查配置: 确认`config.py`中的数据库配置正确

### 问题: 缓存连接失败

可能的原因:
- Docker服务未运行
- Redis容器未启动
- Redis配置错误

解决方案:
- 启动Docker服务
- 手动启动Redis容器: 
  ```sh
  docker run -d --name software-engineering-project-redis -p 6379:6379 redis --requirepass 123456
  ```
- 检查配置: 确认`config.py`中的缓存配置正确

### 问题: 邮件发送失败

可能的原造的原因:
- SMTP配置错误
- 邮箱服务商限制
- 网络问题

解决方案:
- 检查配置: 确认`config.py`中的邮件配置正确
- 使用其他邮箱: 尝试使用其他邮箱服务商
- 检查网络: 确保能够连接到SMTP服务器

### 问题: API认证失败

可能的原因:
- 令牌过期
- 令牌格式错误
- 令牌被篡改

解决方案:
- 重新登录: 获取新的认证令牌
- 检查令牌格式: 确保令牌正确编码
- 检查请求头: 确保使用`Access-Token`请求头

## 9. 开发者指南

本节面向希望参与系统开发的开发者，提供系统扩展和维护的指导。

### 9.1 添加新接口

添加新API接口的步骤:

1. 在`routers`目录下创建新的路由文件或在现有文件中添加新的路由函数
2. 定义路由函数并添加装饰器:
   ```python
   @api.post("/your-path")
   async def your_function(
       request: YourRequestModel,
       access_info: Dict = Depends(jwe_decode),
       db: AsyncSession = Depends(database),
   ):
       # 实现业务逻辑
       return ok(data={"result": "success"})
   ```
3. 在`__init__.py`中注册路由:
   ```python
   from intellide.routers.your_module import api as your_api
   
   router_api.include_router(your_api)
   ```

### 9.2 数据库迁移

当数据模型发生变化时，需要进行数据库迁移:

1. 停止后端服务
2. 修改`model.py`中的数据模型
3. 使用以下命令重置数据库 (注意: 这将删除所有数据):
   ```sh
   docker exec -it software-engineering-project-postgres psql -U postgres -c "DROP DATABASE IF EXISTS ide;"
   ```
4. 重新启动后端服务，系统会自动创建新的数据库和表结构

> **注意**: 在生产环境中，应使用专业的数据库迁移工具，如Alembic，以避免数据丢失。

### 9.3 添加新的依赖服务

如果需要添加新的依赖服务 (如搜索引擎、消息队列等):

1. 在`docker`目录下创建新的启动脚本
2. 在`config.py`中添加相关配置
3. 在`main.py`的`lifespan`函数中添加启动代码

### 9.4 编写测试

系统使用pytest进行测试，添加新测试的步骤:

1. 在`tests`目录下创建新的测试文件
2. 使用pytest fixtures和异步测试功能:
   ```python
   @pytest.mark.asyncio
   async def test_your_function(client):
       response = await client.post("/api/your-path", json={"key": "value"})
       assert response.status_code == 200
       data = response.json()
       assert data["status"] == "success"
   ```
3. 运行测试:
   ```sh
   cd backend/intellide
   python -m pytest
   ```

## 10. API响应格式

所有API响应都遵循统一的格式:

### 成功响应

```json
{
  "status": "success",
  "data": {
    // 响应数据
  }
}
```

- `status`: 固定为`"success"`
- `data`: 包含响应数据的对象，可能是单个值、对象或数组

### 错误响应

```json
{
  "status": "error",
  "message": "错误描述"
}
```

- `status`: 固定为`"error"`
- `message`: 错误描述信息

### 常见HTTP状态码

- `200`: 请求成功
- `400`: 请求参数错误
- `401`: 未授权或认证失败
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## 11. 安全最佳实践

为保证系统安全，请遵循以下最佳实践:

### 11.1 密码安全

- 使用强密码: 至少8个字符，包含大小写字母、数字和特殊字符
- 定期更换密码: 建议每3个月更换一次
- 不共享密码: 每个用户使用独立的账号

### 11.2 API安全

- 保护认证令牌: 不要在不安全的地方存储或传输令牌
- HTTPS: 在生产环境中使用HTTPS加密传输
- 令牌过期: 确保令牌有合理的过期时间

### 11.3 Docker安全

- 限制访问: 不要在公网环境中暴露Docker API
- 更新容器: 定期更新容器镜像以修复安全漏洞
- 最小权限: 使用最小必要的权限运行容器

## 12. 性能优化建议

如果系统性能出现瓶颈，可以考虑以下优化:

### 12.1 数据库优化

- 添加索引: 为常用查询字段添加索引
- 连接池: 增加数据库连接池大小
- 分页查询: 对大数据集使用分页查询

### 12.2 缓存优化

- 增加缓存: 对频繁访问的数据进行缓存
- 调整TTL: 根据数据更新频率调整缓存过期时间
- 分布式缓存: 使用Redis集群提高缓存容量和性能

### 12.3 应用优化

- 异步处理: 将耗时操作放入异步任务
- 水平扩展: 部署多个应用实例并使用负载均衡
- 资源限制: 合理设置容器资源限制，避免单个容器占用过多资源