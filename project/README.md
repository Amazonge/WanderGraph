# WanderGraph — 多智能体旅行规划系统

基于 LangGraph 多智能体 DAG 编排 + 本地大模型，输入一句话即可生成包含景点、天气、住宿、美食、交通、预算、地图可视化的端到端旅行方案。

---

## 技术栈

### 后端（Python 3.11+）

| 层级 | 技术 | 用途 |
|------|------|------|
| **Web 框架** | FastAPI + Uvicorn | 异步 API 服务，支持 SSE 实时进度推送 |
| **多智能体编排** | LangGraph | 12 节点 DAG，fan-out/fan-in 并行，reducer 状态合并 |
| **LLM 接入** | LangChain-OpenAI | 统一 OpenAI/DeepSeek/Ollama 三提供商调用 |
| **本地模型** | Ollama + qwen3:8b | 离线推理，零 API 成本，OpenAI 兼容接口 |
| **工具协议** | MCP (Model Context Protocol) | 门票/酒店/美食外部服务懒连接 + 失败降级 |
| **数据校验** | Pydantic v2 | Schema 契约 + field_validator 智能类型转换 |
| **任务存储** | Redis + hiredis | TaskStore (Hash) + EventPublisher (Pub/Sub)，可选内存模式降级 |
| **HTTP 客户端** | httpx | 异步外部 API 调用 |

### 前端（Node 18+）

| 层级 | 技术 | 用途 |
|------|------|------|
| **框架** | Vue 3.5 + TypeScript | 组合式 API，类型安全 |
| **构建** | Vite 8 | 极速 HMR 热更新 |
| **UI 库** | Ant Design Vue 4 | 企业级组件库 |
| **状态管理** | Pinia | 任务进度状态流转 |
| **路由** | Vue Router 4 | SPA 路由 |
| **地图** | @amap/amap-jsapi-loader | 高德地图，行程可视化 |
| **HTTP** | Axios | SSE 流式响应消费 |
| **动效** | Framer Motion + 自定义 CSS | 进度步骤动画 |

### 算法层（纯 Python 实现）

| 算法 | 解决问题 |
|------|---------|
| **Haversine 球面距离** | 经纬度两点距离计算 |
| **贪心最近邻 + 2-opt** | TSP 路径优化（跳出局部最优） |
| **0-1 背包 DP** | 预算约束下体验价值最大化 |
| **TF-IDF + 协同过滤** | 景点偏好推荐排序 |

### 基础设施

| 组件 | 用途 |
|------|------|
| Ollama | 本地模型服务（端口 11434） |
| Redis | 任务状态持久化 + 事件广播（可选） |
| MCP Server | 门票/酒店/美食数据服务（端口 8001-8003） |

---

## 技术架构

```
用户输入 "帮我规划成都三日游"
         │
    ┌────▼────┐
    │ Frontend │  Vue3 + AntDesign + 高德地图
    │  :5173   │  ← SSE 实时进度流
    └────┬─────┘
         │ HTTP / SSE
    ┌────▼─────┐
    │ Backend  │  FastAPI + Uvicorn :8000
    │  Plan API│  → asyncio.create_task 拉起规划
    └────┬─────┘
         │
    ┌────▼─────────────────────────────────┐
    │   LangGraph 12-Node DAG               │
    │                                       │
    │  coordinator → destination_parser     │
    │       │                               │
    │       ▼ fan-out (并行)                │
    │  [attraction] [weather] [hotel]       │
    │       │      │      │                 │
    │       ▼ sync_tier2 (汇聚)             │
    │       │                               │
    │       ▼ fan-out (并行)                │
    │      [food]  [transport]               │
    │       │      │                         │
    │       ▼ sync_tier3 (汇聚)             │
    │       │                               │
    │  budget → image → compiler            │
    │  → validator → summary → END          │
    └────┬─────────────────────────────────┘
         │
    ┌────▼──────┬──────────┬──────────┐
    │  Ollama   │  MCP      │  Redis   │
    │ qwen3:8b  │  门票/酒店│ 可选     │
    │ :11434    │  /美食    │          │
    └───────────┴──────────┴──────────┘
```

---

## 核心设计

### 1. Reducer 并发状态合并
LangGraph 默认 last_value 通道在并行节点写同一字段时会覆盖。项目用 `Annotated` 标注三类 reducer：
- `node_status: Annotated[dict, merge_dict]` — 字典合并
- `errors: Annotated[list, add]` — 错误累积
- `progress: Annotated[float, last_value]` — 标量取最新

### 2. 七层容错降级
- LLM 输出用 `JSONDecoder.raw_decode` 提取首个完整 JSON，容错 markdown 围栏 + 尾部垃圾
- 数值字段用 Pydantic `field_validator(mode="before")` 从 "50元"/"30°C" 提取数字
- MCP 服务懒连接，失败返回 None 降级
- Redis 不可用时自动降级内存模式
- 无坐标景点降级返回原顺序，不崩溃

### 3. 模型自动选择
`_detect_provider()` 按优先级：显式指定 > 有 API Key 的云端 > 本地 Ollama，零成本本地优先。

---

## 快速启动

```bash
# 1. 启动 Ollama 并拉取模型
ollama serve
ollama pull qwen3:8b

# 2. 一键启动前后端
cd project
python start.py
```
自动拉起后端 :8000、前端 :5173，打开浏览器即用。

### 可选配置（.env）
```env
LLM_PROVIDER=ollama          # ollama / deepseek / openai
OLLAMA_MODEL=qwen3:8b
USE_REDIS=false              # true 启用 Redis 持久化
AMAP_KEY=your_amap_key       # 高德地图
```

---

## 目录结构

```
project/
├── backend/
│   └── app/
│       ├── agents/       # 12 个 Agent 节点实现
│       ├── graph/        # LangGraph DAG 构建 + State 定义
│       ├── models/       # Pydantic Schema 契约
│       ├── utils/        # 算法层（TSP/背包/推荐）+ LLM 客户端
│       ├── mcp/          # MCP 客户端（懒连接 + 降级）
│       ├── infra/        # Redis TaskStore + EventPublisher
│       └── api/routes/   # health + plan + SSE
├── frontend/
│   └── src/
│       ├── views/        # Plan / Recommendations / Reviews
│       ├── components/   # ProgressSteps 等
│       └── stores/       # Pinia 状态
└── start.py              # 一键启动（进程管理 + 编码处理）
```
