"""
WanderGraph 量化指标对比图

展示两个模块的量化指标：
  1. TSP 路径优化 —— 随机/贪心/2-opt/穷举最优 的距离 + 耗时对比
  2. 推荐系统   —— 随机/TF-IDF/协同过滤/混合 的 Precision@K + Recall@K 对比

运行：
  cd WanderGraph
  python doc/metrics_comparison.py

输出：
  doc/tsp_metrics.png
  doc/recommender_metrics.png
"""
import os
import sys
import time
import random
import math
import json
from itertools import permutations

# ── 接入项目真实算法 ──────────────────────────────────────────
PROJECT_BACKEND = os.path.join(os.path.dirname(__file__), "..", "project", "backend")
sys.path.insert(0, PROJECT_BACKEND)

from app.utils.algorithms import (
    haversine,
    total_distance,
    optimize_route_greedy,
    optimize_route_2opt,
    optimize_daily_route,
    ContentRecommender,
    CollaborativeRecommender,
)
from app.utils.llm import parse_json  # 真实解析函数

# ── matplotlib 配置（中文字体 + 协调配色） ─────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["text.color"] = "#333333"
plt.rcParams["axes.labelcolor"] = "#333333"
plt.rcParams["axes.edgecolor"] = "#999999"
plt.rcParams["xtick.color"] = "#555555"
plt.rcParams["ytick.color"] = "#555555"

# 配色（深浅协调，色盲友好）
COLORS = {
    "random":  "#C44E52",   # 红 —— 基线/最差
    "greedy":   "#DD8452",   # 橙 —— 中间
    "2opt":     "#4C72B0",   # 蓝 —— 本项目方案
    "optimal":  "#55A467",   # 绿 —— 最优/上限
    "tfidf":    "#8172B3",   # 紫
    "collab":   "#937860",   # 棕
    "hybrid":   "#4C72B0",   # 蓝（本项目方案，与 2opt 同色呼应）
}

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════
# 模块 1：TSP 路径优化对比
# ═══════════════════════════════════════════════════════════════

# 成都真实景点坐标池（来自 test_algorithms.py 的真实数据 + 扩展）
CHENGDU_SPOTS = [
    {"name": "武侯祠",   "location": {"lat": 30.6460, "lng": 104.0530}},
    {"name": "锦里",     "location": {"lat": 30.6440, "lng": 104.0500}},
    {"name": "宽窄巷子", "location": {"lat": 30.6698, "lng": 104.0636}},
    {"name": "大熊猫基地","location": {"lat": 30.7327, "lng": 104.1477}},
    {"name": "春熙路",   "location": {"lat": 30.6571, "lng": 104.0818}},
    {"name": "都江堰",   "location": {"lat": 30.9950, "lng": 103.9370}},
    {"name": "青城山",   "location": {"lat": 30.8900, "lng": 103.5600}},
    {"name": "文殊院",   "location": {"lat": 30.6710, "lng": 104.0690}},
    {"name": "人民公园", "location": {"lat": 30.6580, "lng": 104.0580}},
    {"name": "望江楼",   "location": {"lat": 30.6430, "lng": 104.0730}},
    {"name": "东郊记忆", "location": {"lat": 30.6700, "lng": 104.1400}},
    {"name": "金沙遗址", "location": {"lat": 30.6820, "lng": 104.0150}},
    {"name": "天府广场", "location": {"lat": 30.6570, "lng": 104.0650}},
    {"name": "浣花溪",   "location": {"lat": 30.6480, "lng": 104.0380}},
    {"name": "欢乐谷",   "location": {"lat": 30.7050, "lng": 104.0950}},
]


def brute_force_optimal(spots):
    """穷举所有排列求最优解（仅小规模可用）"""
    if len(spots) <= 8:
        best, best_d = None, float("inf")
        for perm in permutations(spots):
            d = total_distance(list(perm))
            if d < best_d:
                best_d, best = d, list(perm)
        return best, best_d
    return None, None


def eval_tsp():
    """评估 TSP 各算法在不同规模下的表现"""
    sizes = [5, 8, 10, 12, 15]
    results = {"random": [], "greedy": [], "2opt": [], "optimal": [],
               "time_greedy": [], "time_2opt": []}

    for n in sizes:
        spots = CHENGDU_SPOTS[:n]
        random.seed(42)
        shuffled = spots.copy()
        random.shuffle(shuffled)

        # 随机基线
        d_random = total_distance(shuffled)

        # 贪心
        t0 = time.perf_counter()
        greedy = optimize_route_greedy(shuffled)
        t_greedy = time.perf_counter() - t0
        d_greedy = total_distance(greedy)

        # 2-opt
        t0 = time.perf_counter()
        opt = optimize_route_2opt(greedy)
        t_2opt = time.perf_counter() - t0
        d_2opt = total_distance(opt)

        # 穷举最优（仅 n<=8）
        _, d_opt = brute_force_optimal(shuffled)
        d_opt = d_opt if d_opt is not None else d_2opt  # 大规模用 2-opt 近似

        results["random"].append(d_random)
        results["greedy"].append(d_greedy)
        results["2opt"].append(d_2opt)
        results["optimal"].append(d_opt)
        results["time_greedy"].append(t_greedy)
        results["time_2opt"].append(t_2opt)

    return sizes, results


def plot_tsp(sizes, res):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    fig.patch.set_facecolor("white")

    # ── 左图：总距离对比 ──
    ax1.plot(sizes, res["random"],  "o--", color=COLORS["random"],  lw=1.8, ms=7, label="随机基线")
    ax1.plot(sizes, res["greedy"],  "s-",  color=COLORS["greedy"],   lw=2.0, ms=7, label="贪心最近邻")
    ax1.plot(sizes, res["2opt"],    "^-", color=COLORS["2opt"],     lw=2.2, ms=8, label="贪心 + 2-opt（本项目）")
    ax1.plot(sizes, res["optimal"], "*-", color=COLORS["optimal"],  lw=1.8, ms=10, label="穷举最优（n≤8）")

    # 标注 2-opt 缩减率
    for i, n in enumerate(sizes):
        reduction = (res["random"][i] - res["2opt"][i]) / res["random"][i] * 100
        ax1.annotate(f"-{reduction:.0f}%", (n, res["2opt"][i]),
                     textcoords="offset points", xytext=(0, -18),
                     ha="center", fontsize=8, color=COLORS["2opt"], fontweight="bold")

    ax1.set_xlabel("景点数量")
    ax1.set_ylabel("总移动距离 (km)")
    ax1.set_title("TSP 路径优化：总距离对比", fontsize=13, fontweight="bold", color="#222222", pad=12)
    ax1.legend(loc="upper left", frameon=True, framealpha=0.9, edgecolor="#CCCCCC")
    ax1.grid(True, linestyle="--", alpha=0.4, color="#CCCCCC")
    ax1.set_facecolor("#FAFAFA")

    # ── 右图：耗时对比 ──
    ax2.plot(sizes, res["time_greedy"], "s-", color=COLORS["greedy"], lw=2.0, ms=7, label="贪心最近邻")
    ax2.plot(sizes, res["time_2opt"],   "^-", color=COLORS["2opt"],   lw=2.2, ms=8, label="贪心 + 2-opt")

    ax2.set_xlabel("景点数量")
    ax2.set_ylabel("耗时 (秒)")
    ax2.set_title("TSP 路径优化：耗时对比", fontsize=13, fontweight="bold", color="#222222", pad=12)
    ax2.legend(loc="upper left", frameon=True, framealpha=0.9, edgecolor="#CCCCCC")
    ax2.grid(True, linestyle="--", alpha=0.4, color="#CCCCCC")
    ax2.set_facecolor("#FAFAFA")
    # y 轴从 0 开始
    ax2.set_ylim(bottom=0)

    fig.tight_layout(pad=2.0)
    out = os.path.join(OUT_DIR, "tsp_metrics.png")
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[TSP] 已保存: {out}")
    return out


# ═══════════════════════════════════════════════════════════════
# 模块 2：推荐系统对比
# ═══════════════════════════════════════════════════════════════

# 景点池（带文本描述，用于 TF-IDF）
ATTRACTIONS = [
    {"name": "武侯祠",   "text": "历史 文化 三国 古迹 博物馆"},
    {"name": "锦里",     "text": "古街 美食 购物 文化 夜景"},
    {"name": "大熊猫基地","text": "自然 动物 亲子 熊猫 科普"},
    {"name": "宽窄巷子", "text": "古街 文化 美食 建筑 购物"},
    {"name": "都江堰",   "text": "历史 水利 自然 古迹 工程"},
    {"name": "青城山",   "text": "自然 道教 山林 风景 徒步"},
    {"name": "春熙路",   "text": "购物 美食 现代 商业 夜景"},
    {"name": "文殊院",   "text": "文化 佛教 古迹 寺庙 静谧"},
    {"name": "人民公园", "text": "休闲 文化 茶 公园 本地生活"},
    {"name": "望江楼",   "text": "文化 历史 公园 建筑 古迹"},
    {"name": "东郊记忆", "text": "文创 现代 音乐 工业 购物"},
    {"name": "金沙遗址", "text": "历史 古迹 博物馆 文化 考古"},
]

# 4 组偏好查询 + 对应 ground truth（人工标注的"应推荐"景点）
QUERIES = [
    {"query": "历史 古迹",        "gt": {"武侯祠", "都江堰", "金沙遗址", "文殊院"}},
    {"query": "美食 购物",        "gt": {"锦里", "春熙路", "宽窄巷子"}},
    {"query": "自然 亲子",        "gt": {"大熊猫基地", "青城山", "都江堰"}},
    {"query": "文化 古街",        "gt": {"锦里", "宽窄巷子", "武侯祠"}},
]

# 用户交互历史（用于协同过滤，留一法：每个用户留 1 个景点作为应推荐）
USER_HISTORY = {
    "user_A": {"visited": ["武侯祠", "都江堰"], "holdout": "金沙遗址"},   # 历史偏好
    "user_B": {"visited": ["锦里", "春熙路"], "holdout": "宽窄巷子"},     # 美食偏好
    "user_C": {"visited": ["大熊猫基地", "青城山"], "holdout": "都江堰"}, # 自然偏好
    "user_D": {"visited": ["武侯祠", "锦里"], "holdout": "宽窄巷子"},     # 文化偏好
}


def eval_recommender():
    """评估 4 种推荐策略的 Precision@3 和 Recall@3"""
    methods = ["random", "tfidf", "collab", "hybrid"]
    precision = {m: [] for m in methods}
    recall = {m: [] for m in methods}

    rec = ContentRecommender()
    rec.fit(ATTRACTIONS, text_key="text")

    # 构建协同过滤交互矩阵
    cf = CollaborativeRecommender()
    for uid, info in USER_HISTORY.items():
        items = [{"id": v, "name": v} for v in info["visited"]]
        cf.add_interaction(uid, items)

    # 每个用户对应一个偏好查询
    query_map = ["历史 古迹", "美食 购物", "自然 亲子", "文化 古街"]
    user_ids = list(USER_HISTORY.keys())

    for i, q in enumerate(QUERIES):
        query = q["query"]
        gt = q["gt"]
        uid = user_ids[i]

        # 1) 随机基线
        random.seed(i)
        rand_ranked = ATTRACTIONS.copy()
        random.shuffle(rand_ranked)
        rand_top3 = {r["name"] for r in rand_ranked[:3]}

        # 2) TF-IDF
        tfidf_results = rec.recommend(query, top_k=3)
        tfidf_top3 = {r["name"] for r in tfidf_results}

        # 3) 协同过滤
        cf_results = cf.recommend(uid, top_k=3)
        cf_top3 = {r["name"] for r in cf_results}

        # 4) 混合：TF-IDF ∪ CF，按出现频次 + TF-IDF 分数加权
        hybrid_scores = {}
        for rank, r in enumerate(tfidf_results):
            hybrid_scores[r["name"]] = hybrid_scores.get(r["name"], 0) + (3 - rank) * 2
        for r in cf_results:
            hybrid_scores[r["name"]] = hybrid_scores.get(r["name"], 0) + 1.5
        hybrid_top3 = set(sorted(hybrid_scores, key=lambda k: -hybrid_scores[k])[:3])

        for m, top3 in [("random", rand_top3), ("tfidf", tfidf_top3),
                        ("collab", cf_top3), ("hybrid", hybrid_top3)]:
            hit = len(top3 & gt)
            precision[m].append(hit / 3)
            recall[m].append(hit / len(gt))

    avg_p = {m: sum(precision[m]) / len(precision[m]) for m in methods}
    avg_r = {m: sum(recall[m]) / len(recall[m]) for m in methods}
    return avg_p, avg_r


def plot_recommender(avg_p, avg_r):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    fig.patch.set_facecolor("white")

    methods = ["random", "tfidf", "collab", "hybrid"]
    labels = ["随机基线", "TF-IDF 内容", "协同过滤", "混合推荐（本项目）"]
    colors = [COLORS["random"], COLORS["tfidf"], COLORS["collab"], COLORS["hybrid"]]

    x = range(len(methods))
    width = 0.35
    bars1 = ax.bar([i - width/2 for i in x], [avg_p[m] for m in methods],
                   width, label="Precision@3", color=colors, alpha=0.85, edgecolor="white", linewidth=1.2)
    bars2 = ax.bar([i + width/2 for i in x], [avg_r[m] for m in methods],
                   width, label="Recall@3", color=colors, alpha=0.45, edgecolor="white", linewidth=1.2,
                   hatch="//")

    # 数值标注
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.02, f"{h:.2f}",
                ha="center", va="bottom", fontsize=9, color="#333333", fontweight="bold")
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.02, f"{h:.2f}",
                ha="center", va="bottom", fontsize=9, color="#666666")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("指标值")
    ax.set_ylim(0, 1.0)
    ax.set_title("推荐系统：Precision@3 / Recall@3 对比", fontsize=13, fontweight="bold", color="#222222", pad=12)
    ax.legend(loc="upper right", frameon=True, framealpha=0.9, edgecolor="#CCCCCC")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4, color="#CCCCCC")
    ax.set_facecolor("#FAFAFA")

    fig.tight_layout(pad=2.0)
    out = os.path.join(OUT_DIR, "recommender_metrics.png")
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[推荐] 已保存: {out}")
    return out


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  WanderGraph 量化指标对比图生成")
    print("=" * 60)

    print("\n[1/2] TSP 路径优化对比 ...")
    sizes, tsp_res = eval_tsp()
    tsp_out = plot_tsp(sizes, tsp_res)

    print("\n[2/2] 推荐系统对比 ...")
    avg_p, avg_r = eval_recommender()
    rec_out = plot_recommender(avg_p, avg_r)

    print("\n" + "=" * 60)
    print("  完成！图表已保存到 doc/ 目录")
    print("=" * 60)
