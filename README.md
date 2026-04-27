# Smart_LLM_Test_Framework

> 面向复杂业务的工业级大模型 Agent 与 RAG 智能评测底座。

面向 AI 初创公司 CTO 与技术负责人：如果你的 Agent 正在走向生产，这个框架不是“加分项”，而是上线前的生死线。它将不可控的模型行为压缩为可审计、可回归、可门禁的工程资产。  

---

## Why This Exists 🔥

工业现场里，失败从来不是“答错一句话”这么简单，而是连锁事故：

- **Agent 行为非确定性**：同题多答，线上策略漂移不可见，版本回归形同虚设。  
- **多步 Tool Use 黑盒**：你只看到了最终回答，却看不到中间决策与工具链路。  
- **Token 成本失控**：所有样例都上裁判模型，评测预算在 CI 里被静默吞噬。  

`Smart_LLM_Test_Framework` 的目标很直接：把“主观体验”变成“结构化质量门”，把“随机对话”变成“可追责轨迹”。  

---

## Core Capabilities 🧠

### 1) 白盒级 Trajectory 观测（SSE Event Tapping）

在 `core/requests_client.py` 中对 Dify 流式响应进行底层事件解析，实时捕获并归档关键事件：

- `message` / `agent_message`：拼接最终可见回答  
- `agent_thought`：记录 Agent 思考与工具意图  
- `tool_response`：记录工具侧真实返回数据  

这意味着你不再只做“结果断言”，而是具备对 Agent 推理与工具调用路径的白盒审计能力。  

### 2) LLM-as-a-Judge 裁判引擎（Prompt-Policy Matrix）

在 `evaluators/llm_judge.py` 中构建了 10+ 套评测模板（如 `rbac_escalation`、`tool_calling`、`rag_closed_book`、`factuality`、`security` 等），将“主观退化”翻译为结构化判定：

- 统一输出 `score / is_pass / reason`  
- 强制 JSON 协议，兼容脏输出清洗与容错解析  
- 被测模型与裁判模型分离，避免同模自评偏置  

### 3) 端云隔离双层 Mock 沙盒（Mock-as-Code）

在 `core/wiremock_client.py` 中提供用例级动态注入与重置能力：

- `inject_mock(json_file_path)`：伴生状态注入  
- `reset_all()`：测试前后自动清场  

配合 `test_cases/conftest.py` 的 `autouse` fixture，实现“每条用例都在干净靶场执行”，用于模拟极端工况与网络熔断前后的行为稳定性。  

### 4) Cost-aware 前置短路拦截（Rule First, Judge Later）

在 `test_cases/test_single_turn.py` 中，对安全类题目加入规则前置短路：

- 若回答命中拒答关键词，直接判通过  
- 不进入 LLM Judge 深评，显著降低裁判模型调用成本  

这是工业评测里最关键的成本治理策略之一：**把高成本评估留给高风险样本**。  

---

## Architecture Layout 🗂️

```text
Smart_LLM_Test_Framework/
├─ core/
│  ├─ requests_client.py        # Dify/OpenAI 双客户端 + SSE 事件采集
│  └─ wiremock_client.py        # Mock 注入/重置
├─ evaluators/
│  └─ llm_judge.py              # LLM-as-a-Judge 多模板裁判引擎
├─ test_cases/
│  ├─ conftest.py               # 全局 fixture + 自动 reset
│  ├─ test_single_turn.py       # 单轮评测 + 成本短路策略
│  └─ test_agent_routing.py     # Agent 动态路由与工具行为审计
├─ data/
│  ├─ base.yml
│  ├─ security.yml
│  ├─ factuality.yml
│  ├─ rag.yml
│  ├─ agent.yml
│  ├─ agent_routing.yml
│  └─ mocks/
│     ├─ weather_level_2.json
│     ├─ weather_level_6.json
│     └─ weather_level_8.json
├─ utils/
│  ├─ SmartConfig.py
│  ├─ data_loader.py
│  └─ logger.py
├─ pytest.ini
└─ .env.example
```

---

## Tech Stack ⚙️

### Current (已落地)

- **Language/Test**: Python, Pytest  
- **LLM Access**: Requests, Dify API, OpenAI-Compatible API  
- **Mock Sandbox**: WireMock  
- **Data & Config**: YAML (PyYAML), dotenv, logging/colorlog  

### Roadmap (规划中)

- **Playwright**：补齐端到端 Agent 交互链路回归（UI/Browser-based flow）  
- **Pandas**：扩展离线评测统计、分层切片与趋势报表能力  

---

## Quick Start 🚀

### 1) 准备环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install pytest requests python-dotenv pyyaml colorlog
```

### 2) 配置 `.env`

参考 `.env.example` 配置以下关键项：

- `API_PLATFORM`（`dify` / `openai`）  
- `LLM_API_KEY`, `LLM_BASE_URL`  
- `JUDGE_API_KEY`, `JUDGE_BASE_URL`, `JUDGE_MODEL`  
- `REQUEST_TIMEOUT`  

### 3) 执行评测

```bash
pytest
```

或仅执行关键场景：

```bash
pytest test_cases/test_single_turn.py -vs
pytest test_cases/test_agent_routing.py -vs
```

---

## CI Quality Gate Blueprint 🛡️

将此框架作为发布前置门禁时，建议采用以下流水线顺序：

1. **基础语义回归**（`base.yml`）  
2. **安全与事实性防线**（`security.yml` + `factuality.yml`）  
3. **RAG 闭卷与 grounding**（`rag.yml`）  
4. **Agent 工具路由与 RBAC 越权审计**（`agent*.yml` + WireMock）  
5. **门禁判定**：任一高风险用例失败即阻断发布  

你得到的不是“测试报告”，而是一套可持续迭代的 **Agent 质量防火墙**。  

---

## Positioning Statement 🎯

`Smart_LLM_Test_Framework` 的价值，不在于“又一个测试脚本集合”，而在于为复杂业务建立了一条可工业化复用的 Agent 质量供应链：  
**可观测、可裁判、可隔离、可控成本、可门禁上线。**
