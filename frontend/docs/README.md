# 前端使用指南

## 目录结构

```text
frontend/intelligent-ide/
 ├── .gitignore # Git 忽略规则
 ├── .vscodeignore # 打包时需要排除的文件和文件夹
 ├── CHANGELOG.md # 更新日志 
 ├── esbuild.js # 构建配置（使用 esbuild） 
 ├── package.json # 扩展清单（包括命令、视图、贡献等） 
 ├── README.md # 本文档 
 ├── tsconfig.json # TypeScript 编译配置 
 └── src/ 
  ├── commands/ 
  │ ├── loginCommand.ts # 登录命令的声明及逻辑调用 
  │ ├── registerCommand.ts # 注册命令的声明及逻辑调用 
  │ └── updateComman.ts # 更新命令的声明及逻辑调用 
  ├── resources/ 
  │ └── configs/ 
  │  └── config.ts # API 端点等配置信息 
  ├── services/ 
  │ └── userService.ts # 与后端交互的业务逻辑（如登录、注册、更新） 
  ├── test/ 
  │ └── extension.test.ts # 扩展功能的基本测试（未完成）
  ├── utils/ 
  │ └── responseParser.ts # 辅助解析后端返回的数据 
  └── extension.ts # 主入口：注册所有命令及设置视图
```

## debug/运行方法

1. 使用**vscode**打开本项目
2. 移动到`/intelligent-ide`文件夹目录下，不能在其他文件夹下
3. 运行`npm install`安装依赖
4. 打开/extension.ts文件，按f5，会自动开始编译运行扩展程序。如果出现让你选择debugger，并且没有extension development类似选项，请检查是否在`intelligent-ide`文件夹下。
5. 新窗口打开，标题会有[Extension Development Host]字样，并且debug `console中有 Congratulations, your extension "intelligent-ide" is now active!` 信息，说明运行成功。

## 使用方法

- 命令
  - 使用`Ctrl + Shift + P`打开vscode命令行，在这里输入命令。如果没有出现以下命令，也请检查自己是否在`intelligent-ide`文件夹下。
    - `intelligent-ide.login`：登录命令
    - `intelligent-ide.register`：注册命令
    - `intelligent-ide.update`：更新命令
