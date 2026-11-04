"""
algorithms.py — 项目核心算法

1. 路线优化（TSP 近似）：贪心最近邻 + 2-opt 局部搜索
2. 预算分配（背包 DP）：0-1 背包 + 启发式比例分配
3. 混合推荐（TF-IDF + 协同过滤）：内容推荐 + 协同过滤
"""
import math
from collections import Counter
from typing import Optional


# ═══════════════════════════════════════════════════════════
# 算法 1：路线优化 — TSP 近似（贪心 + 2-opt）
# ═══════════════════════════════════════════════════════════

def haversine(loc1: tuple[float, float], loc2: tuple[float, float]) -> float:
    """Haversine 公式：计算地球上两点间的球面距离（km）

    Args:
        loc1: (纬度, 经度)
        loc2: (纬度, 经度)

    Returns:
        距离（公里）
    """
    lat1, lng1 = math.radians(loc1[0]), math.radians(loc1[1])
    lat2, lng2 = math.radians(loc2[0]), math.radians(loc2[1])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _spot_loc(spot: dict) -> tuple[float, float]:
    """提取景点坐标。

    None 安全：LLM 常把 location 返回成 null（键存在但值为 None），
    此时 spot.get("location", {}) 返回 None 而非默认 {}，再 .get 会抛
    'NoneType' object has no attribute 'get'（见 ISSUES #16）。
    用 `... or {}` 把 None 也兜成空 dict。
    """
    loc = (spot or {}).get("location") or {}
    return (loc.get("lat", 0), loc.get("lng", 0))


def total_distance(route: list[dict]) -> float:
    """计算路线总距离（km）"""
    dist = 0.0
    for i in range(len(route) - 1):
        dist += haversine(_spot_loc(route[i]), _spot_loc(route[i + 1]))
    return dist


def optimize_route_greedy(spots: list[dict]) -> list[dict]:
    """贪心最近邻 TSP 近似 — O(n²)

    从第一个景点出发，每次选最近的未访问景点。
    简单高效，解的质量约为最优解的 1.25 倍。

    Args:
        spots: 景点列表，每个含 location.lat, location.lng

    Returns:
        重排后的景点列表
    """
    if len(spots) <= 2:
        return list(spots)

    visited = [spots[0]]
    remaining = list(spots[1:])

    while remaining:
        current = visited[-1]
        current_loc = _spot_loc(current)
        nearest_idx = min(
            range(len(remaining)),
            key=lambda i: haversine(current_loc, _spot_loc(remaining[i]))
        )
        visited.append(remaining.pop(nearest_idx))

    return visited


def optimize_route_2opt(route: list[dict]) -> list[dict]:
    """2-opt 局部搜索优化

    在贪心结果基础上，反复尝试"反转一段路径"来缩短总距离。
    终止条件：一轮遍历中没有任何改进。

    时间复杂度：O(n² × 迭代次数)
    空间复杂度：O(n)

    Args:
        route: 已有路线（如贪心输出）

    Returns:
        优化后的路线
    """
    if len(route) <= 3:
        return list(route)

    route = list(route)
    improved = True
    iterations = 0

    while improved and iterations < 100:  # 限制最大迭代
        improved = False
        iterations += 1

        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                # 计算交换边 (i-1, i) 和 (j, j+1) 前后的距离差
                # 注意：j+1 可能越界（最后一个点没有下一条边）
                d_old = haversine(_spot_loc(route[i - 1]), _spot_loc(route[i]))
                if j + 1 < len(route):
                    d_old += haversine(_spot_loc(route[j]), _spot_loc(route[j + 1]))

                d_new = haversine(_spot_loc(route[i - 1]), _spot_loc(route[j]))
                if j + 1 < len(route):
                    d_new += haversine(_spot_loc(route[i]), _spot_loc(route[j + 1]))

                if d_new < d_old - 0.001:  # 浮点容差
                    # 反转 route[i:j+1]
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True

    return route


def optimize_daily_route(spots: list[dict]) -> list[dict]:
    """组合策略：贪心 + 2-opt（推荐入口）

    先用贪心快速得到一个可行解，再用 2-opt 局部优化。

    Args:
        spots: 当天的景点列表

    Returns:
        地理位置最优排列的景点列表
    """
    if len(spots) <= 1:
        return list(spots)

    # 检查是否有坐标数据（None 安全：location 可能是 null）
    has_location = all(
        (s or {}).get("location") and
        (s or {}).get("location", {}).get("lat") and
        (s or {}).get("location", {}).get("lng")
        for s in spots
    )
    if not has_location:
        return list(spots)  # 无坐标数据，不优化

    route = optimize_route_greedy(spots)
    route = optimize_route_2opt(route)
    return route


# ═══════════════════════════════════════════════════════════
# 算法 2：预算分配 — 0-1 背包 DP + 启发式分配
# ═══════════════════════════════════════════════════════════

def optimize_budget_knapsack(
    items: list[dict],
    budget: float,
) -> list[dict]:
    """0-1 背包动态规划：在预算约束下最大化体验价值

    经典 DP 问题的旅行场景应用：
    - 物品 = 可选体验项目（景点、餐饮、活动）
    - 重量 = 费用
    - 价值 = 体验评分
    - 背包容量 = 总预算

    Args:
        items: 可选项目列表 [{"name": str, "cost": float, "value": float}, ...]
               value: 1-10 体验评分
        budget: 总预算（元）

    Returns:
        选中的项目列表（最优组合）
    """
    if not items or budget <= 0:
        return []

    n = len(items)
    budget_int = max(1, int(budget))

    # dp[i][w] = 考虑前 i 个项目、预算为 w 时的最大价值
    dp = [[0.0] * (budget_int + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        cost = max(1, int(items[i - 1]["cost"]))
        value = items[i - 1]["value"]
        for w in range(budget_int + 1):
            if cost <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - cost] + value)
            else:
                dp[i][w] = dp[i - 1][w]

    # 回溯选出的项目
    selected = []
    w = budget_int
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(items[i - 1])
            w -= max(1, int(items[i - 1]["cost"]))

    return list(reversed(selected))


def allocate_budget(
    total: float,
    days: int,
    traveler_count: int = 1,
    city_level: str = "moderate",
) -> dict:
    """启发式预算分配：按城市等级 + 经验比例自动规划

    Args:
        total: 总预算（元）
        days: 旅行天数
        traveler_count: 出行人数
        city_level: 城市消费水平 "budget" / "moderate" / "luxury"

    Returns:
        {"hotel": float, "food": float, "transport": float,
         "tickets": float, "shopping": float, "total": float}
    """
    # 不同消费水平的比例调整
    ratios = {
        "budget":   {"hotel": 0.30, "food": 0.30, "transport": 0.15, "tickets": 0.15, "shopping": 0.10},
        "moderate": {"hotel": 0.35, "food": 0.25, "transport": 0.15, "tickets": 0.15, "shopping": 0.10},
        "luxury":   {"hotel": 0.40, "food": 0.20, "transport": 0.10, "tickets": 0.15, "shopping": 0.15},
    }
    r = ratios.get(city_level, ratios["moderate"])

    allocation = {}
    for key, ratio in r.items():
        allocation[key] = round(total * ratio, 2)

    allocation["total"] = sum(allocation.values())
    allocation["per_day"] = round(total / max(days, 1), 2)
    allocation["per_person"] = round(total / max(traveler_count, 1), 2)

    return allocation


# ═══════════════════════════════════════════════════════════
# 算法 3：混合推荐 — TF-IDF 内容推荐 + 协同过滤
# ═══════════════════════════════════════════════════════════

class ContentRecommender:
    """基于内容的推荐：TF-IDF + 余弦相似度

    原理：
    1. 对每个景点的文本描述做 TF-IDF 向量化
    2. 用户偏好也转为 TF-IDF 向量
    3. 计算用户向量与每个景点向量的余弦相似度
    4. 按相似度排序返回 Top-K

    不依赖 sklearn，纯 Python 实现 TF-IDF。
    """

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.tfidf_matrix: list[dict[int, float]] = []
        self.items: list[dict] = []

    def fit(self, items: list[dict], text_key: str = "text"):
        """构建 TF-IDF 矩阵

        Args:
            items: 景点列表 [{"name": ..., "text": "自然 风光 山水"}, ...]
            text_key: 文本字段名
        """
        self.items = items
        n = len(items)

        # 分词（简单空格分割）
        docs = [item.get(text_key, "").split() for item in items]

        # 构建词汇表 + 计算 IDF
        df = Counter()  # 文档频率
        for doc in docs:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1
                if term not in self.vocab:
                    self.vocab[term] = len(self.vocab)

        self.idf = {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}

        # 计算每个文档的 TF-IDF 向量（稀疏表示）
        self.tfidf_matrix = []
        for doc in docs:
            tf = Counter(doc)
            total = len(doc) if doc else 1
            vec = {}
            for term, count in tf.items():
                if term in self.vocab:
                    idx = self.vocab[term]
                    tfidf = (count / total) * self.idf.get(term, 1.0)
                    vec[idx] = tfidf
            self.tfidf_matrix.append(vec)

    def recommend(self, query: str, top_k: int = 5) -> list[dict]:
        """根据查询文本推荐最相关的景点

        Args:
            query: 用户偏好的文本描述（如 "美食 历史 文化"）
            top_k: 返回数量

        Returns:
            按相关度排序的景点列表
        """
        if not self.items:
            return []

        # 查询向量化
        query_terms = query.split()
        query_tf = Counter(query_terms)
        query_total = len(query_terms) if query_terms else 1
        query_vec = {}
        for term, count in query_tf.items():
            if term in self.vocab:
                idx = self.vocab[term]
                query_vec[idx] = (count / query_total) * self.idf.get(term, 1.0)

        # 计算余弦相似度
        scores = []
        for i, doc_vec in enumerate(self.tfidf_matrix):
            score = self._cosine_similarity(query_vec, doc_vec)
            scores.append((i, score))

        # 排序取 Top-K
        scores.sort(key=lambda x: -x[1])
        return [self.items[i] for i, _ in scores[:top_k]]

    @staticmethod
    def _cosine_similarity(vec1: dict[int, float], vec2: dict[int, float]) -> float:
        """余弦相似度（稀疏向量）"""
        dot = sum(vec1[k] * vec2.get(k, 0) for k in vec1)
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


class CollaborativeRecommender:
    """简易协同过滤：基于用户历史行为

    原理：
    1. 构建 用户-景点 交互矩阵
    2. 计算用户间的 Jaccard 相似度
    3. 找到最相似的 K 个用户
    4. 推荐他们喜欢但当前用户没去过的景点
    """

    def __init__(self):
        self.user_items: dict[str, set[str]] = {}  # user_id → {item_ids}
        self.item_names: dict[str, dict] = {}       # item_id → item_data

    def add_interaction(self, user_id: str, items: list[dict]):
        """记录用户与景点的交互（去过的景点）

        Args:
            user_id: 用户 ID
            items: 景点列表 [{"id": "a1", "name": "武侯祠", ...}, ...]
        """
        if user_id not in self.user_items:
            self.user_items[user_id] = set()

        for item in items:
            item_id = item.get("id", item.get("name", ""))
            self.user_items[user_id].add(item_id)
            self.item_names[item_id] = item

    def recommend(self, user_id: str, top_k: int = 5) -> list[dict]:
        """为指定用户推荐景点

        Args:
            user_id: 目标用户
            top_k: 返回数量

        Returns:
            推荐的景点列表
        """
        if user_id not in self.user_items or len(self.user_items) < 2:
            return []

        target_items = self.user_items[user_id]

        # 计算与所有其他用户的 Jaccard 相似度
        similarities = []
        for other_id, other_items in self.user_items.items():
            if other_id == user_id:
                continue
            intersection = len(target_items & other_items)
            union = len(target_items | other_items)
            if union > 0:
                similarities.append((other_id, intersection / union))

        # 按相似度排序
        similarities.sort(key=lambda x: -x[1])

        # 从相似用户的景点中推荐（排除已去过的）
        recommended_ids = []
        for other_id, sim in similarities[:5]:
            for item_id in self.user_items[other_id]:
                if item_id not in target_items and item_id not in recommended_ids:
                    recommended_ids.append(item_id)
                    if len(recommended_ids) >= top_k:
                        break
            if len(recommended_ids) >= top_k:
                break

        return [self.item_names[item_id] for item_id in recommended_ids if item_id in self.item_names]

    def get_similar_users(self, user_id: str, top_k: int = 3) -> list[tuple[str, float]]:
        """获取最相似的用户"""
        if user_id not in self.user_items:
            return []

        target_items = self.user_items[user_id]
        similarities = []
        for other_id, other_items in self.user_items.items():
            if other_id == user_id:
                continue
            intersection = len(target_items & other_items)
            union = len(target_items | other_items)
            if union > 0:
                similarities.append((other_id, intersection / union))

        similarities.sort(key=lambda x: -x[1])
        return similarities[:top_k]


def build_user_text(items: list[dict]) -> str:
    """从景点列表构建用户偏好文本（用于 TF-IDF 查询）"""
    categories = []
    keywords = []
    for item in items:
        cat = item.get("category", "")
        if cat:
            categories.append(cat)
        tips = item.get("tips", [])
        keywords.extend(tips[:2])

    counter = Counter(categories + keywords)
    return " ".join(term for term, _ in counter.most_common(10))
