# Code Review Agent - AI 代码审查代理

基于 LangGraph 和 LangChain 构建的智能代码审查工具，采用并行工作流架构，实现代码的静态分析、安全扫描和风格检查的并发执行。

## ✨ 功能特性

- **静态分析**：基于 AST 的代码结构分析，包括函数/类统计、圈复杂度估算、过长函数检测、裸 except 检测
- **安全扫描**：检测 SQL 注入风险、硬编码密钥、危险函数调用（eval/exec/pickle 等）
- **风格检查**：基于 PEP 8 标准的代码风格审查
- **并行执行**：三路审查并发进行，大幅降低端到端延迟
- **智能汇总**：自动整合三份审查报告，生成结构化的最终报告

## 🏗️ 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 工作流引擎 | LangGraph | 并行工作流编排 |
| LLM 框架 | LangChain | 大语言模型交互 |
| 语言模型 | OpenAI API | GPT-4o-mini |
| 静态分析 | Python AST | 内置语法树解析 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install langgraph langchain python-dotenv
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_API_NAME=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1
```

### 3. 运行审查

```python
from component_assembly import review_app

# 待审查的代码
code = """
def example_function(x):
    if x > 0:
        return x * 2
    else:
        return x
"""

# 执行审查
result = review_app.invoke({
    "code": code,
    "messages": []
})

print(result["final_report"])
```

## 📁 项目结构

```
code_review_agent/
├── review_state.py        # 状态定义（TypedDict）
├── distribution_nodes.py  # 分发节点（并行调度）
├── review_nodes.py        # 审查节点（调用 LLM）
├── sink_nodes.py          # 汇总节点（生成报告）
├── component_assembly.py  # 工作流组装
├── model.py               # LLM 模型配置
├── static_review.py       # 静态分析工具
├── security_review.py     # 安全扫描工具
├── style_review.py        # 风格检查工具
├── test.py                # 测试文件
└── .env                   # 环境变量配置
```

### 文件职责说明

| 文件 | 职责 |
|------|------|
| `review_state.py` | 定义工作流状态结构（TypedDict） |
| `distribution_nodes.py` | 实现分发逻辑，使用 Send API 并行调度 |
| `review_nodes.py` | 封装与 LLM 的交互，执行智能审查 |
| `sink_nodes.py` | 汇总三路审查结果，生成最终报告 |
| `component_assembly.py` | 组装完整的 StateGraph 工作流 |
| `model.py` | LLM 模型初始化和配置 |
| `static_review.py` | 基于 AST 的静态分析工具 |
| `security_review.py` | 安全漏洞扫描工具 |
| `style_review.py` | PEP 8 风格检查工具 |

## 🔄 工作流架构

项目采用 **Fan-out → Fan-in** 并行模式：

```
START
  │
  ▼
┌─────────────┐
│  dispatch   │  ← 接收待审查代码
└──────┬──────┘
       │
       ├────────────────┬────────────────┐
       │                │                │
       ▼                ▼                ▼
┌───────────┐    ┌───────────┐    ┌───────────┐
│ static    │    │ security  │    │   style   │
│ analysis  │    │   scan    │    │  check    │
└─────┬─────┘    └─────┬─────┘    └─────┬─────┘
      │                │                │
      └────────────────┼────────────────┘
                       │
                       ▼
              ┌───────────────┐
              │generate_report│ ← 汇总三份报告
              └───────┬───────┘
                      │
                      ▼
                    END
```

### 并行机制说明

基于 LangGraph 的 **Send API** 实现并发调度：

1. `dispatch` 节点返回 `[Send("static_analysis", ...), Send("security_scan", ...), Send("style_check", ...)]`
2. LangGraph 在同一个 super-step 中将三个任务并发执行
3. `generate_report` 节点等待所有上游节点完成后才激活（fan-in 语义）
4. 最终汇总三份审查结果生成完整报告

## ⚙️ 配置说明

### 静态分析配置

在 `static_review.py` 中可调整：

```python
MAX_CODE_SIZE = 1024 * 1024  # 最大代码大小：1MB
COMPLEXITY_THRESHOLD = 10     # 圈复杂度警告阈值
MAX_FUNCTION_LINES = 50       # 函数体最大行数
```

### LLM 配置

在 `model.py` 中可调整模型参数：

```python
llm = init_chat_model(
    model=os.getenv("OPENAI_API_NAME"),
    model_provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
    temperature=0.0,  # 低温度确保结果一致性
    model_kwargs={
        "extra_body": {"thinking": {"type": "enabled"}}
    }
)
```

## 🛡️ 安全特性

- **输入大小限制**：防止超大代码导致的 DoS 攻击
- **异常处理**：完善的语法错误和运行时异常处理
- **数据隔离**：每个审查节点独立处理，状态分离

## 📊 审查报告示例

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    代码审查报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【静态分析】
代码总行数：42
函数数量：3（main, process_data, validate_input）
类数量：1（DataProcessor）
发现问题：1 个
  - 函数 `process_data` 圈复杂度为 12，建议拆分

【安全扫描】
发现 0 个安全问题
未发现明显的安全漏洞。

【风格检查】
发现 2 个风格问题
  - 第 15 行：缩进应为 4 空格，实际为 2 空格
  - 第 28 行：运算符两侧应有空格

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总体评估：需要改进
建议：考虑拆分 `process_data` 函数并修复风格问题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🧪 测试示例

```python
from component_assembly import review_app

# 测试代码
test_code = """
def vulnerable_function(user_input):
    import subprocess
    subprocess.call("echo " + user_input, shell=True)
    return "Done"
"""

# 执行审查
result = review_app.invoke({
    "code": test_code,
    "messages": []
})

# 输出安全扫描结果
print(result["security_result"])
```

## 📝 开发指南

### 添加新的审查维度

1. 创建新的审查工具（如 `performance_review.py`）
2. 在 `review_state.py` 中添加新的状态字段
3. 在 `distribution_nodes.py` 中添加新的 Send 节点
4. 在 `review_nodes.py` 中实现审查节点
5. 在 `component_assembly.py` 中注册新节点并添加边

### 扩展审查规则

- **静态分析**：在 `static_review.py` 中添加新的检测规则
- **安全扫描**：在 `security_review.py` 中添加新的正则模式
- **风格检查**：在 `style_review.py` 中添加新的风格规则

## 📄 许可证

MIT License

## 🤝 贡献


##剩余任务
- [ ] 增加代码语法检查功能
- [ ] 进一步增加文件类型的处理
- [ ] 增加skills处理
