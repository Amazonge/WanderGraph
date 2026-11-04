# 测试流程与测试案例

---

## 一、测试分层

```
Layer 1: 算法单元测试      tests/test_algorithms.py    30 个用例  不需要 LLM/Redis
Layer 2: 模型单元测试      tests/test_models.py        11 个用例  不需要 LLM/Redis
Layer 3: Agent 集成测试    手动运行                     需要 LLM (Ollama)
Layer 4: API 端到端测试    curl / Swagger               需要 LLM + 后端启动
Layer 5: 前端联调测试      浏览器操作                    需要全栈启动
```

---

## 二、Layer 1：算法单元测试（核心）

### 运行方式

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/test_algorithms.py -v
```

### 测试覆盖（30 个用例）

#### 1.1 Haversine 距离公式（3 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_same_point | 同一坐标 | 0.0 | 零距离 |
| test_known_distance | 天府广场→武侯祠 | 1-5km | 实际距离正确 |
| test_long_distance | 成都→北京 | 1400-1800km | 远距离正确 |

#### 1.2 路线优化 TSP（7 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_greedy_reduces_distance | 5 个成都景点乱序 | 优化后距离 ≤ 乱序距离 | 贪心有效 |
| test_2opt_improves_greedy | 贪心输出 | 2-opt 后距离 ≤ 贪心距离 | 2-opt 改进 |
| test_optimize_daily_route | 5 个景点 | 返回完整列表 | 入口函数正确 |
| test_empty_input | [] | [] | 空输入处理 |
| test_single_spot | 1 个景点 | 原样返回 | 单点处理 |
| test_no_location_data | 无坐标景点 | 原样返回 | 降级处理 |
| test_optimization_metrics | 随机排列 | 打印优化指标 | 效果可量化 |

**测试数据（成都真实坐标）**：
```python
chengdu_spots = [
    {"name": "武侯祠",     "location": {"lat": 30.6460, "lng": 104.0530}},
    {"name": "锦里",       "location": {"lat": 30.6440, "lng": 104.0500}},
    {"name": "宽窄巷子",   "location": {"lat": 30.6698, "lng": 104.0636}},
    {"name": "大熊猫基地", "location": {"lat": 30.7327, "lng": 104.1477}},
    {"name": "春熙路",     "location": {"lat": 30.6571, "lng": 104.0818}},
]
```

#### 1.3 预算背包 DP（5 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_basic_knapsack | 3 项，预算 150 | 总费用 ≤ 150，总价值 ≥ 15 | DP 最优性 |
| test_zero_budget | 空列表，预算 0 | [] | 零预算处理 |
| test_all_affordable | 2 项，预算 100 | 全选 | 充足预算 |
| test_tight_budget | 3 项，预算 100 | 总费用 ≤ 100 | 紧张预算取舍 |
| test_knapsack_optimality | 3 项，预算 50 | 总价值 ≥ 20 | 最优解验证 |

**测试数据**：
```python
items = [
    {"name": "武侯祠", "cost": 50, "value": 9},
    {"name": "火锅",   "cost": 120, "value": 10},
    {"name": "串串",   "cost": 60, "value": 7},
]
budget = 150
# 最优：武侯祠+串串 (cost=110, value=16) 优于 火锅 (cost=120, value=10)
```

#### 1.4 预算启发式分配（4 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_basic_allocation | 5000/3天/1人 | total=5000 | 总额正确 |
| test_per_person | 6000/3天/2人 | per_person=3000 | 人均正确 |
| test_city_levels | budget vs luxury | luxury 酒店费更高 | 消费水平差异 |
| test_allocation_sums_to_total | 3000/2天 | 各项之和 = 3000 | 预算守恒 |

#### 1.5 TF-IDF 内容推荐（6 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_fit_and_recommend | 5 景点，查"历史 古迹" | 武侯祠/都江堰在前 | TF-IDF 匹配 |
| test_preference_match | 查"美食" | 锦里/宽窄巷子在前 | 偏好匹配 |
| test_empty_query | 空查询 | 返回 ≤ 3 | 空查询处理 |
| test_no_items | 无景点 | 返回 [] | 空数据处理 |
| test_cosine_similarity | 相同向量 | ≈ 1.0 | 相似度计算 |
| test_cosine_orthogonal | 正交向量 | = 0.0 | 正交性 |

#### 1.6 协同过滤（4 个）

| 用例 | 输入 | 期望 | 验证点 |
|------|------|------|--------|
| test_recommend_for_user | user_A | 推荐宽窄巷子 | 相似用户推荐 |
| test_exclude_visited | user_A | 不含已去过景点 | 排除已访问 |
| test_similar_users | user_A | user_B 最相似 | Jaccard 相似度 |
| test_new_user | 新用户 | 返回 [] | 冷启动处理 |

---

## 三、Layer 2：模型单元测试

```bash
.venv/Scripts/python.exe -m pytest tests/test_models.py -v
```

11 个用例覆盖 Pydantic 模型的校验逻辑（Field 约束、model_validator、嵌套模型）。

---

## 四、Layer 3：Agent 集成测试（需要 Ollama）

### 前提

```bash
ollama serve                           # Ollama 运行中
ollama list                            # 确认 qwen3:8b 可用
```

### 测试 3.1：DestinationParserAgent

```bash
cd backend
.venv/Scripts/python.exe -c "
import asyncio
from app.agents.destination import DestinationParserAgent

async def test():
    agent = DestinationParserAgent()
    state = {
        'user_query': '下周去成都玩3天，预算5000，喜欢美食',
        'errors': [], 'node_status': {}, 'progress': 0.0
    }
    result = await agent(state)
    print(f'目的地: {result.get(\"destination\")}')
    print(f'日期: {result.get(\"travel_dates\")}')
    print(f'预算: {result.get(\"budget\")}')
    print(f'偏好: {result.get(\"preferences\")}')
    assert result.get('destination') and '成都' in result['destination']
    assert result.get('travel_dates', {}).get('start')
    print('PASS')

asyncio.run(test())
"
```

### 测试 3.2：BudgetEstimateAgent（含背包优化）

```bash
.venv/Scripts/python.exe -c "
import asyncio
from app.agents.budget import BudgetEstimateAgent

async def test():
    agent = BudgetEstimateAgent()
    state = {
        'travel_dates': {'start': '2026-06-06', 'end': '2026-06-08'},
        'traveler_count': 1,
        'budget': 5000,
        'attractions': [
            {'name': '武侯祠', 'ticket_price': 50, 'rating': 4.6},
            {'name': '大熊猫基地', 'ticket_price': 55, 'rating': 4.8},
        ],
        'food_plan': {'must_try_dishes': [
            {'name': '火锅', 'price_range': '80-150元/人', 'is_local_specialty': True},
        ]},
        'hotel_recommendations': [{'price_range': '¥200-400/晚'}],
        'errors': [], 'node_status': {}
    }
    result = await agent(state)
    est = result.get('budget_estimate', {})
    print(f'总预算: {est.get(\"total\")}')
    print(f'分配策略: {est.get(\"allocation_strategy\")}')
    print(f'背包优化体验: {est.get(\"optimized_experiences\")}')
    assert est.get('total', 0) > 0
    assert est.get('allocation_strategy')
    print('PASS')

asyncio.run(test())
"
```

### 测试 3.3：ItineraryCompilerAgent（含路线优化）

```bash
.venv/Scripts/python.exe -c "
import asyncio
from app.agents.compiler import ItineraryCompilerAgent

async def test():
    agent = ItineraryCompilerAgent()
    state = {
        'destination': '成都市',
        'travel_dates': {'start': '2026-06-06', 'end': '2026-06-08'},
        'traveler_count': 1,
        'preferences': ['美食', '历史'],
        'attractions': [
            {'name': '武侯祠', 'category': '历史', 'location': {'lat': 30.646, 'lng': 104.053}},
            {'name': '锦里', 'category': '文化', 'location': {'lat': 30.644, 'lng': 104.050}},
            {'name': '大熊猫基地', 'category': '自然', 'location': {'lat': 30.733, 'lng': 104.148}},
            {'name': '宽窄巷子', 'category': '文化', 'location': {'lat': 30.670, 'lng': 104.064}},
        ],
        'weather_info': {'summary': '多云 22-28°C'},
        'hotel_recommendations': [{'name': '酒店A', 'price_range': '¥300/晚'}],
        'food_plan': {'must_try_dishes': [{'name': '火锅', 'price_range': '100元'}]},
        'budget_estimate': {'total': 1450},
        'errors': [], 'node_status': {}
    }
    result = await agent(state)
    itin = result.get('itinerary', [])
    route_opt = result.get('route_optimization', {})
    print(f'行程天数: {len(itin)}')
    print(f'路线优化: {route_opt}')
    assert len(itin) > 0
    assert route_opt.get('reduction_percent', 0) >= 0
    print('PASS')

asyncio.run(test())
"
```

### 测试 3.4：完整 DAG 端到端

```bash
.venv/Scripts/python.exe -c "
import asyncio
from app.graph.builder import build_travel_graph

async def test():
    graph = build_travel_graph()
    result = await graph.ainvoke({
        'user_query': '下周去成都玩3天，预算5000，喜欢美食',
        'errors': [], 'node_status': {}, 'progress': 0.0,
    })
    print(f'目的地: {result.get(\"destination\")}')
    print(f'行程天数: {len(result.get(\"itinerary\", []))}')
    print(f'路线优化: {result.get(\"route_optimization\", {})}')
    print(f'预算: {result.get(\"budget_estimate\", {}).get(\"total\")}')
    print(f'摘要: {result.get(\"summary\", \"\")[:100]}...')
    assert result.get('destination')
    assert len(result.get('itinerary', [])) > 0
    print('PASS')

asyncio.run(test())
"
```

---

## 五、Layer 4：API 端到端测试

### 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 测试 4.1：Swagger UI

浏览器打开 `http://localhost:8000/docs`，在 `POST /api/plan` 中试用：

```json
{"query": "下周去成都玩3天，预算5000，喜欢美食"}
```

### 测试 4.2：curl 测试

```bash
# 提交任务
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "下周去成都玩3天，预算5000"}'
# 返回 {"task_id":"xxx","status":"pending"}

# 监听 SSE（等待 30-60 秒）
curl http://localhost:8000/api/plan/{task_id}/stream

# 查看结果
curl http://localhost:8000/api/plan/{task_id}
```

### 测试 4.3：健康检查

```bash
curl http://localhost:8000/api/health
# {"status":"ok","version":"0.2.0","llm_provider":"ollama","redis":"error:..."}
```

---

## 六、Layer 5：前端联调测试

### 启动全栈

```bash
# 终端 1：后端
cd backend && uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend && pnpm dev
```

### 测试流程

```
1. 打开 http://localhost:5173
2. 首页输入 "下周去成都玩3天，预算5000，喜欢美食"
3. 点击 "开始规划"
4. 观察：
   ✅ 进度条逐步更新（12 个 Agent）
   ✅ 每个 Agent 完成后标记绿色
   ✅ 执行完成后显示行程卡片
5. 检查行程内容：
   ✅ 3 天行程，每天有活动和餐饮
   ✅ 景点顺序合理（路线优化生效）
   ✅ 预算汇总正确
6. 测试导出：
   ✅ JSON 下载
   ✅ PNG 截图
7. 测试历史：
   ✅ 切换到历史记录页
   ✅ 能看到刚才的规划
   ✅ 点击能回到行程详情
```

---

## 七、测试结果记录模板

```
测试日期: ____
测试环境: Windows 11 / Python 3.11 / Ollama qwen3:8b

Layer 1 算法单元测试:   ___/30 通过
Layer 2 模型单元测试:   ___/11 通过
Layer 3 Agent 集成测试: ___/4  通过
Layer 4 API 测试:       ___/3  通过
Layer 5 前端联调:       ___/7  通过

总计: ___/55 通过
```
