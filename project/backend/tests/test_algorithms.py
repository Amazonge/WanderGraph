"""
test_algorithms.py — 三大核心算法测试

运行:
  cd backend
  python -m pytest tests/test_algorithms.py -v

覆盖:
  1. 路线优化（TSP 贪心 + 2-opt）
  2. 预算分配（背包 DP + 启发式）
  3. 混合推荐（TF-IDF + 协同过滤）
"""
import pytest
from app.utils.algorithms import (
    haversine,
    total_distance,
    optimize_route_greedy,
    optimize_route_2opt,
    optimize_daily_route,
    allocate_budget,
    optimize_budget_knapsack,
    ContentRecommender,
    CollaborativeRecommender,
    build_user_text,
)


# ═══════════════════════════════════════════════════════════
# 1. 路线优化测试
# ═══════════════════════════════════════════════════════════

class TestHaversine:
    """Haversine 距离公式"""

    def test_same_point(self):
        assert haversine((30.65, 104.05), (30.65, 104.05)) == 0.0

    def test_known_distance(self):
        # 成都天府广场 → 武侯祠，约 1.7km
        d = haversine((30.6570, 104.0650), (30.6460, 104.0530))
        assert 1.0 < d < 5.0

    def test_long_distance(self):
        # 成都 → 北京，约 1500km
        d = haversine((30.57, 104.07), (39.90, 116.40))
        assert 1400 < d < 1800


class TestRouteOptimization:
    """路线优化：贪心 + 2-opt"""

    @pytest.fixture
    def chengdu_spots(self):
        """成都 5 个景点的真实坐标"""
        return [
            {"name": "武侯祠", "location": {"lat": 30.6460, "lng": 104.0530}},
            {"name": "锦里", "location": {"lat": 30.6440, "lng": 104.0500}},
            {"name": "宽窄巷子", "location": {"lat": 30.6698, "lng": 104.0636}},
            {"name": "大熊猫基地", "location": {"lat": 30.7327, "lng": 104.1477}},
            {"name": "春熙路", "location": {"lat": 30.6571, "lng": 104.0818}},
        ]

    def test_greedy_reduces_distance(self, chengdu_spots):
        """贪心算法应比乱序更优"""
        import random
        random.seed(42)
        shuffled = chengdu_spots.copy()
        random.shuffle(shuffled)

        greedy = optimize_route_greedy(shuffled)
        d_before = total_distance(shuffled)
        d_after = total_distance(greedy)

        assert d_after <= d_before

    def test_2opt_improves_greedy(self, chengdu_spots):
        """2-opt 应在贪心基础上进一步优化"""
        greedy = optimize_route_greedy(chengdu_spots)
        opt = optimize_route_2opt(greedy)

        d_greedy = total_distance(greedy)
        d_opt = total_distance(opt)

        # 2-opt 不会比贪心更差
        assert d_opt <= d_greedy + 0.01

    def test_optimize_daily_route(self, chengdu_spots):
        """组合策略入口"""
        result = optimize_daily_route(chengdu_spots)
        assert len(result) == len(chengdu_spots)
        assert all(s["name"] in [x["name"] for x in chengdu_spots] for s in result)

    def test_empty_input(self):
        assert optimize_daily_route([]) == []

    def test_single_spot(self):
        spots = [{"name": "武侯祠", "location": {"lat": 30.64, "lng": 104.05}}]
        assert optimize_daily_route(spots) == spots

    def test_no_location_data(self):
        """无坐标数据时不做优化，原样返回"""
        spots = [{"name": "武侯祠"}, {"name": "锦里"}]
        result = optimize_daily_route(spots)
        assert len(result) == 2

    def test_optimization_metrics(self, chengdu_spots):
        """验证优化效果指标"""
        import random
        random.seed(99)
        shuffled = chengdu_spots.copy()
        random.shuffle(shuffled)

        d_before = total_distance(shuffled)
        optimized = optimize_daily_route(shuffled)
        d_after = total_distance(optimized)

        reduction = (d_before - d_after) / d_before * 100 if d_before > 0 else 0
        print(f"\n  路线优化: {d_before:.1f}km → {d_after:.1f}km (减少 {reduction:.1f}%)")
        # 优化后不应更差
        assert d_after <= d_before + 0.01


# ═══════════════════════════════════════════════════════════
# 2. 预算分配测试
# ═══════════════════════════════════════════════════════════

class TestBudgetKnapsack:
    """0-1 背包 DP"""

    def test_basic_knapsack(self):
        """基础背包：预算内选最有价值的"""
        items = [
            {"name": "武侯祠", "cost": 50, "value": 9},
            {"name": "火锅", "cost": 120, "value": 10},
            {"name": "串串", "cost": 60, "value": 7},
        ]
        selected = optimize_budget_knapsack(items, budget=150)

        total_cost = sum(i["cost"] for i in selected)
        total_value = sum(i["value"] for i in selected)
        assert total_cost <= 150
        # 最优组合：武侯祠+串串 (cost=110, value=16) 优于 火锅 (cost=120, value=10)
        assert total_value >= 15

    def test_zero_budget(self):
        assert optimize_budget_knapsack([], 0) == []

    def test_all_affordable(self):
        """预算充足时全选"""
        items = [
            {"name": "A", "cost": 10, "value": 5},
            {"name": "B", "cost": 20, "value": 6},
        ]
        selected = optimize_budget_knapsack(items, budget=100)
        assert len(selected) == 2

    def test_tight_budget(self):
        """预算紧张时取舍"""
        items = [
            {"name": "贵但值", "cost": 90, "value": 10},
            {"name": "便宜一般", "cost": 30, "value": 4},
            {"name": "便宜也好", "cost": 30, "value": 5},
        ]
        selected = optimize_budget_knapsack(items, budget=100)
        total_cost = sum(i["cost"] for i in selected)
        assert total_cost <= 100

    def test_knapsack_optimality(self):
        """验证背包的最优性"""
        items = [
            {"name": "A", "cost": 10, "value": 6},
            {"name": "B", "cost": 20, "value": 10},
            {"name": "C", "cost": 30, "value": 12},
        ]
        selected = optimize_budget_knapsack(items, budget=50)
        total_value = sum(i["value"] for i in selected)
        total_cost = sum(i["cost"] for i in selected)
        assert total_cost <= 50
        # 最优应该是 B+C (value=22, cost=50) 或 A+B (value=16, cost=30)
        assert total_value >= 20


class TestBudgetAllocation:
    """启发式预算分配"""

    def test_basic_allocation(self):
        result = allocate_budget(total=5000, days=3, traveler_count=1)
        assert result["total"] == 5000
        assert result["hotel"] > 0
        assert result["food"] > 0
        assert result["per_day"] == round(5000 / 3, 2)

    def test_per_person(self):
        result = allocate_budget(total=6000, days=3, traveler_count=2)
        assert result["per_person"] == 3000

    def test_city_levels(self):
        budget_result = allocate_budget(5000, 3, 1, "budget")
        luxury_result = allocate_budget(5000, 3, 1, "luxury")
        # 奢华模式酒店占比更高
        assert luxury_result["hotel"] > budget_result["hotel"]

    def test_allocation_sums_to_total(self):
        result = allocate_budget(3000, 2, 1)
        categories = result["hotel"] + result["food"] + result["transport"] + result["tickets"] + result["shopping"]
        assert abs(categories - 3000) < 0.01


# ═══════════════════════════════════════════════════════════
# 3. 混合推荐测试
# ═══════════════════════════════════════════════════════════

class TestContentRecommender:
    """TF-IDF 内容推荐"""

    @pytest.fixture
    def attractions(self):
        return [
            {"name": "武侯祠", "text": "历史 文化 三国 古迹"},
            {"name": "锦里", "text": "古街 美食 购物 文化"},
            {"name": "大熊猫基地", "text": "自然 动物 亲子 熊猫"},
            {"name": "宽窄巷子", "text": "古街 文化 美食 建筑"},
            {"name": "都江堰", "text": "历史 水利 自然 古迹"},
        ]

    def test_fit_and_recommend(self, attractions):
        rec = ContentRecommender()
        rec.fit(attractions, text_key="text")

        results = rec.recommend("历史 古迹", top_k=3)
        assert len(results) <= 3
        # 历史相关的应该排在前面
        names = [r["name"] for r in results]
        assert "武侯祠" in names or "都江堰" in names

    def test_preference_match(self, attractions):
        rec = ContentRecommender()
        rec.fit(attractions, text_key="text")

        # 偏好"美食"
        results = rec.recommend("美食", top_k=2)
        names = [r["name"] for r in results]
        assert "锦里" in names or "宽窄巷子" in names

    def test_empty_query(self, attractions):
        rec = ContentRecommender()
        rec.fit(attractions, text_key="text")
        results = rec.recommend("", top_k=3)
        assert len(results) <= 3

    def test_no_items(self):
        rec = ContentRecommender()
        rec.fit([], text_key="text")
        assert rec.recommend("test", top_k=5) == []

    def test_cosine_similarity(self):
        vec1 = {0: 1.0, 1: 2.0}
        vec2 = {0: 1.0, 1: 2.0}
        sim = ContentRecommender._cosine_similarity(vec1, vec2)
        assert abs(sim - 1.0) < 0.001  # 完全相似

    def test_cosine_orthogonal(self):
        vec1 = {0: 1.0}
        vec2 = {1: 1.0}
        sim = ContentRecommender._cosine_similarity(vec1, vec2)
        assert sim == 0.0  # 正交


class TestCollaborativeRecommender:
    """协同过滤"""

    @pytest.fixture
    def recommender(self):
        rec = CollaborativeRecommender()
        # 模拟用户历史
        rec.add_interaction("user_A", [
            {"id": "wuhou", "name": "武侯祠"},
            {"id": "jinli", "name": "锦里"},
            {"id": "panda", "name": "大熊猫基地"},
        ])
        rec.add_interaction("user_B", [
            {"id": "wuhou", "name": "武侯祠"},
            {"id": "jinli", "name": "锦里"},
            {"id": "kuanzhai", "name": "宽窄巷子"},
        ])
        rec.add_interaction("user_C", [
            {"id": "panda", "name": "大熊猫基地"},
            {"id": "dujiangyan", "name": "都江堰"},
        ])
        return rec

    def test_recommend_for_user(self, recommender):
        results = recommender.recommend("user_A", top_k=2)
        names = [r["name"] for r in results]
        # user_A 没去过宽窄巷子，但相似用户 user_B 去过
        assert "宽窄巷子" in names

    def test_exclude_visited(self, recommender):
        results = recommender.recommend("user_A", top_k=10)
        visited = {"武侯祠", "锦里", "大熊猫基地"}
        for r in results:
            assert r["name"] not in visited

    def test_similar_users(self, recommender):
        similar = recommender.get_similar_users("user_A", top_k=2)
        assert len(similar) > 0
        # user_B 和 user_A 共同去过武侯祠、锦里，相似度最高
        assert similar[0][0] == "user_B"

    def test_new_user(self):
        rec = CollaborativeRecommender()
        rec.add_interaction("user_A", [{"id": "a", "name": "A"}])
        results = rec.recommend("new_user", top_k=5)
        assert results == []  # 新用户无历史


class TestBuildUserText:
    """用户偏好文本构建"""

    def test_basic(self):
        items = [
            {"category": "历史", "tips": ["适合拍照"]},
            {"category": "美食", "tips": ["推荐火锅"]},
            {"category": "历史", "tips": ["需要讲解"]},
        ]
        text = build_user_text(items)
        assert "历史" in text
        assert "美食" in text
