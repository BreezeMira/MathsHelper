# 小沃 - AI 数学助手

基于 ReAct 范式与 Wolfram Mathematica 引擎的智能数学问题求解 Agent

---

## 项目简介

小沃是一个基于 ReAct（Reasoning + Acting）范式的智能数学助手，通过集成大语言模型和 Wolfram Mathematica 计算引擎，能够自动完成数学问题的求解、表达式渲染和可视化展示。

核心能力：
- 符号计算：积分、微分、极限、级数、矩阵运算
- 方程求解：代数方程、方程组、丢番图方程、微分方程
- 数据可视化：函数图像、3D 曲面、散点图
- 表达式渲染：将复杂数学公式渲染为高清图片
- 智能推理：基于 ReAct 范式的多步推理与工具调用

---

## 系统架构

```
用户交互层 (CLI)
        |
        v
Agent 核心 (ReActAgent)
  - 对话历史管理 (messages)
  - ReAct 循环控制 (思考 -> 行动 -> 观察)
  - 步数管理 + 审查机制
        |
        +------------------+
        |                  |
        v                  v
记忆模块              工具集 (ToolExecutor)
(messages)            - run_wolfram
存储完整对话历史       - test_connection
                      - set_timeout
                      - get_timeout
        |                  |
        +------------------+
                |
                v
外部依赖与存储
  - LLM 服务 (OpenAI API)
  - Wolfram 引擎 (wolframscript.exe)
  - 文件存储 (plots/ , expressions/)
```

---

## 环境配置

### 1. 环境要求

| 依赖 | 版本/说明 |
|------|----------|
| Python | 3.8 及以上 |
| Wolfram Mathematica | 需包含 wolframscript.exe |
| OpenAI API Key | 或兼容 API 服务 |

### 2. 安装依赖

```bash
pip install openai python-dotenv
```

### 3. 配置文件

复制 `.env_example.txt` 为 `.env`，填写以下配置：

```
# Wolfram Mathematica 引擎路径（必需）
WOLFRAMSCRIPT_PATH=D:\Wolfram Mathematica\15.0\wolframscript.exe

# LLM 服务配置（必需）
OPENAI_MODEL=deepseek-v4-pro
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.deepseek.com

# 可选配置
REASONING_MODE=1          # 1: 开启思考模式, 0: 关闭（默认0）
MAX_STEPS=5               # 最大推理步数（默认5）
LLM_TIME_OUT=60           # LLM 请求超时秒数（默认60）
```

### 4. 系统提示词

确保 `config/system_prompt.txt` 文件存在，该文件定义了 Agent 的角色、行为规范和 Skill 规则。

---

## 运行说明

### 启动 Agent

```bash
python agent.py
```

### 交互操作

| 操作 | 说明 |
|------|------|
| 输入数学问题 | Agent 自动进行推理和计算 |
| `exit` 或 `quit` | 退出程序 |
| `Ctrl+C` | 强制中断 |

### 使用示例

用户输入：
```
求解方程 x^3 - 3x^2 + 2 = 0 的所有根，并绘制函数图像
```

Agent 执行流程：
```
[第1步] 思考：先用 Wolfram 求解方程
[工具调用] run_wolfram(code="Solve[x^3 - 3x^2 + 2 == 0, x]", output_type="math_text")
[观察] {{x -> 1}, {x -> 1 + Sqrt[3]}, {x -> 1 - Sqrt[3]}}

[第2步] 思考：已求得三个根，绘制函数图像
[工具调用] run_wolfram(code="Plot[x^3 - 3x^2 + 2, {x, -2, 3}]", output_type="plot_image")
[观察] plots/plot_a1b2c3d4.png

[第3步] 思考：完成求解和绘图，给出最终答案
```

输出：
```
【结论】
方程 x^3 - 3x^2 + 2 = 0 的三个根为：
x = 1, x = 1 + sqrt(3), x = 1 - sqrt(3)

【函数图像】
plots/plot_a1b2c3d4.png

【解的公式】
expressions/expr_e5f6g7h8.png
```

---

## 工具说明

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| run_wolfram | 执行 Wolfram 代码 | code（必填）, output_type（必填） |
| test_connection | 测试 Wolfram 引擎连接 | 无 |
| set_timeout | 设置执行超时（秒） | seconds（必填，>0） |
| get_timeout | 获取当前超时设置 | 无 |

### run_wolfram 的 output_type 参数

| 模式 | 用途 | 返回 |
|------|------|------|
| math_text | 纯文本计算结果 | 计算结果的字符串 |
| plot_image | 生成数学图像 | 图片文件路径 |
| wolfram_expression_image | 渲染表达式为图片 | 图片文件路径 |

重要：wolfram_expression_image 模式传入的是表达式结果，而非计算命令。传入 Solve[] 或 Reduce[] 会渲染命令本身而非解。

---

## 目录结构

```
.
├── agent.py                 # Agent 核心实现
├── tools.py                 # 工具执行器
├── config/
│   └── system_prompt.txt    # 系统提示词
├── plots/                   # 数学图像存储目录（自动创建）
├── expressions/             # 表达式图片存储目录（自动创建）
├── .env                     # 环境变量配置
├── .env_example.txt         # 配置示例
└── README.md               # 项目文档
```

---

## 设计摘要

### 范式选择：ReAct

系统采用 ReAct（Reasoning + Acting）范式，通过"思考 -> 行动 -> 观察"循环实现数学问题求解。思考步骤由 LLM 完成（`call_llm()`），行动步骤通过工具执行（`_process_tool_calls()` + `ToolExecutor`），观察结果写回对话历史（`messages`）。

### 记忆机制

采用工作记忆，通过 `messages` 列表存储完整对话历史（system/user/assistant/tool 角色），每次 LLM 调用均基于完整上下文。当前为内存存储，无跨会话持久化。

### Skill 体系

Skill 内置于系统提示词中，包括：
- 数学计算 Skill：积分、微分、极限、矩阵运算
- 方程求解 Skill：代数方程、丢番图方程、微分方程
- 绘图 Skill：函数图像、散点图、3D 曲面
- 表达式渲染 Skill：长公式图片生成
- 超时处理 Skill：超时降级策略
- 输出规范 Skill：CLI 格式规范

---

## 系统局限与改进方向

### 当前局限

1. 缺少恶意代码防护机制，Wolfram 代码可能存在注入风险
2. 未分离服务端与客户端，无法支持远程访问和多用户并发
3. 记忆缺少持久化，会话结束后即丢失
4. 错误恢复能力有限，无法区分错误类型采取不同策略

### 改进方向

| 优先级 | 改进项 | 说明 |
|--------|--------|------|
| P0 | 代码安全检查 | 建立多层检查：静态模式匹配 + AST 语义分析 + 沙箱隔离 + 操作白名单 |
| P1 | 服务端-客户端分离 | 重构为 RESTful API 服务，支持多用户并发 |
| P2 | 记忆持久化与压缩 | 引入数据库存储和上下文摘要机制 |
| P3 | 智能错误恢复 | 建立错误分类体系，区分语法错误、超时、无解等场景 |
| P4 | 请求级隔离 | 建立 Agent 实例池，支持并发请求隔离 |