# 项目代码度量报告

## 使用的工具

本项目使用[Radon](https://radon.readthedocs.io/)进行代码度量分析。Radon是一个Python工具，可以计算各种代码度量指标，包括：

- 代码行数统计（原始代码行数、逻辑代码行数等）
- 圈复杂度（Cyclomatic Complexity）
- 维护指数（Maintainability Index）
- Halstead度量（难度、工作量等）

## 执行的命令

以下是用于获取度量结果的命令：

```bash
# 安装radon工具
pip install radon

# 计算代码行数
radon raw -s .

# 计算圈复杂度
radon cc -a .
```

## 度量结果概要

### 1. 代码行数 (Lines of Code)

| 指标 | 数值 |
|------|------|
| 总行数 (LOC) | 7,667 |
| 逻辑代码行数 (LLOC) | 2,964 |
| 源代码行数 (SLOC) | 5,138 |
| 注释行数 (Comments) | 536 |
| 空白行数 (Blank) | 1,102 |
| 注释比例 (C % L) | 7% |

### 2. 源代码文件数

通过分析，项目共包含**43个Python源代码文件**。

### 3. 圈复杂度 (Cyclomatic complexity)

| 指标 | 数值 |
|------|------|
| 分析的代码块（类、函数、方法）数量 | 268 |
| 平均圈复杂度 | 2.44 (等级A) |

圈复杂度等级分布：
- A级（低复杂度，1-5）：绝大多数
- B级（中复杂度，6-10）：少量
- C级（高复杂度，11-20）：极少数

### 4. 依赖项数量

| 依赖类型 | 数量 |
|---------|------|
| 主要依赖项 | 22 |
| 开发依赖项 | 7 |
| 总计 | 29 |

## 详细分析

### 复杂度较高的模块

以下是复杂度较高的模块：

1. `backend\intellide\docker\startup.py` 中的 `startup` 函数（复杂度C）
2. `backend\intellide\routers\course_directory_entry.py` 中的 `course_directory_entry_get` 函数（复杂度C）
3. `backend\intellide\routers\course_homework.py` 中的 `course_homework_submission_get` 函数（复杂度C）

### 代码分布情况

代码主要集中在以下目录：
- `backend\intellide\routers\` - 包含大量业务逻辑和API路由
- `backend\intellide\tests\` - 包含大量测试代码
- `backend\intellide\database\` - 包含数据库模型和操作

## 结论

1. 项目规模中等，代码总量约7,667行。
2. 代码质量良好，平均圈复杂度为2.44（A级），表明大多数函数和方法设计简单清晰。
3. 依赖管理合理，总共使用了29个依赖项，覆盖了开发和生产环境的需求。
4. 注释比例为7%，可以考虑增加适当的注释以提高代码可读性。
