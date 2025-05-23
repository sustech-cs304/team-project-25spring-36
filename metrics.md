# 项目代码度量报告

# 后端

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

## 前端

### 使用的工具

本项目前端部分使用了 **Sonar Scanner** 进行代码质量分析，并将结果上传至 [SonarCloud](https://sonarcloud.io/)，一个可视化的在线质量管理平台。

### 执行的命令

```bash
# 安装 Sonar Scanner
npm install -g sonar-scanner

# 执行分析（需配置 sonar-project.properties）
sonar-scanner

#测试覆盖率
vscode-test -- --coverage
```

```properties
# sonar-project.properties
sonar.projectKey=local-project
sonar.sources=src
sonar.exclusions=**/node_modules/**/*,**/test/**/*.ts
sonar.tests=src/test
sonar.test.inclusions=**/*.test.ts,**/*.spec.ts
sonar.test.exclusions=**/node_modules/**/*
sonar.host.url=https://sonarcloud.io
sonar.organization=similar2
sonar.scm.disabled=true
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.lcov.reportPaths=coverage/lcov.info
```

------

### 度量结果概要

#### 1. 代码行数 (Lines of Code)

| 指标                   | 数值  |
| ---------------------- | ----- |
| 总行数 (Lines)         | 6,151 |
| 有效代码行 (LOC)       | 4,529 |
| 新增代码行 (New LOC)   | 1,385 |
| 注释行 (Comment Lines) | 922   |
| 注释比例 (%)           | 16.9% |
| 语句数 (Statements)    | 2,065 |
| 函数数 (Functions)     | 272   |
| 类数 (Classes)         | 5     |
| 文件数 (Files)         | 29    |



#### 2. 圈复杂度 (Complexity)

| 指标                   | 数值 |
| ---------------------- | ---- |
| 圈复杂度 (Cyclomatic)  | 919  |
| 认知复杂度 (Cognitive) | 959  |



#### 3. 代码重复 (Duplication)

| 指标                        | 数值 |
| --------------------------- | ---- |
| 重复行数 (Duplicated Lines) | 155  |
| 重复代码块 (Blocks)         | 8    |
| 重复文件 (Files)            | 2    |
| 重复度 (Density)            | 2.5% |



#### 4. 代码异味与技术债务

| 指标                            | 数值     |
| ------------------------------- | -------- |
| Code Smells                     | 167      |
| 技术债务 (Technical Debt)       | 2天2小时 |
| 债务比 (Debt Ratio)             | 0.8%     |
| 到达A等级所需努力 (Effort to A) | 0        |



#### 5. 覆盖率 (Coverage)

| 指标       | 百分比 |
| ---------- | ------ |
| 语句覆盖率 | 68.67% |
| 分支覆盖率 | 73.52% |
| 函数覆盖率 | 13.23% |
| 行覆盖率   | 68.67% |



------

## 结论

1. **代码规模适中**：前端共计约 6,151 行代码，分布在 29 个文件中，模块化良好。
2. **代码质量稳定**：圈复杂度较高（919），但尚处于可控范围，认知复杂度略高（959），可能表明部分函数设计偏复杂，可做适当重构。
3. **注释比例较高**：达到 16.9%，利于协作与维护。
4. **重复代码率较低**：仅 2.5%，整体可接受。
5. **技术债务轻微**：仅约两天工时，债务比为 0.8%，处于优秀状态。
6. **单元测试覆盖中等偏上**：语句和分支覆盖率接近 70%，但函数覆盖率（13.23%）较低，建议增强函数级别测试以提升鲁棒性。
7. **需注意的风险点**：
   - 存在 167 处 code smells，可逐步修复以优化可读性和可维护性。
