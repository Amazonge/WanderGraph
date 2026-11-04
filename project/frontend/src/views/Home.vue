<template>
  <div class="home-container">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          WanderGraph
        </h1>
        <p class="hero-subtitle">AI 多智能体旅行规划系统</p>
        <p class="hero-description">
          告诉我你想去哪里，我们的 AI 助手将为你量身定制完美的旅行计划
        </p>

        <!-- 主要功能展示 -->
        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <AimOutlined />
            </div>
            <div class="feature-content">
              <h3>智能规划</h3>
              <p>基于 AI 分析你的喜好和预算</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <EnvironmentOutlined />
            </div>
            <div class="feature-content">
              <h3>景点地图</h3>
              <p>可视化展示行程路线和景点位置</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <WalletOutlined />
            </div>
            <div class="feature-content">
              <h3>预算管理</h3>
              <p>详细分析各项费用，合理规划预算</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-container">
        <h2 class="search-title">开始你的旅行规划</h2>
        <p class="search-subtitle">描述你的旅行需求，让 AI 为你生成专属行程</p>

        <div class="search-box">
          <a-textarea
            v-model:value="query"
            :rows="4"
            placeholder="例：下周想去成都玩3天，预算5000，喜欢美食和历史古迹"
            size="large"
            class="search-input"
          />

          <div class="examples">
            <span class="examples-label">快速示例：</span>
            <div class="examples-list">
              <a-tag
                v-for="example in examples"
                :key="example"
                class="example-tag"
                @click="query = example"
              >
                {{ example }}
              </a-tag>
            </div>
          </div>

          <a-button
            type="primary"
            size="large"
            class="search-button"
            :loading="loading"
            :disabled="query.length < 5"
            @click="handleSubmit"
          >
            <span v-if="!loading">开始规划</span>
            <span v-else>生成中...</span>
          </a-button>
        </div>
      </div>
    </div>

    <!-- 功能介绍 -->
    <div class="features-section">
      <h2 class="section-title">为什么选择 WanderGraph？</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-card-icon">
            <TeamOutlined />
          </div>
          <h3>多智能体协作</h3>
          <p>多个 AI 专智能体协同工作，为你提供全面、准确的旅行建议</p>
        </div>
        <div class="feature-card">
          <div class="feature-card-icon">
            ⚡
          </div>
          <h3>快速响应</h3>
          <p>实时生成行程，让你快速获得详细的旅行计划</p>
        </div>
        <div class="feature-card">
          <div class="feature-card-icon">
            <SmileOutlined />
          </div>
          <h3>个性化定制</h3>
          <p>根据你的偏好、预算和时间，打造独一无二的旅行体验</p>
        </div>
        <div class="feature-card">
          <div class="feature-card-icon">
            <BarChartOutlined />
          </div>
          <h3>数据分析</h3>
          <p>深入分析景点、天气、交通等因素，确保行程最优</p>
        </div>
      </div>
    </div>

    <!-- 统计数据 -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">10K+</div>
          <div class="stat-label">用户信赖</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">50+</div>
          <div class="stat-label">热门城市</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">24/7</div>
          <div class="stat-label">在线服务</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">100%</div>
          <div class="stat-label">满意度</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { message } from 'ant-design-vue'
import {
  AimOutlined,
  EnvironmentOutlined,
  WalletOutlined,
  TeamOutlined,
  SmileOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const query = ref('')
const loading = ref(false)
const features = ref([
  { icon: '🎯', title: '智能规划', description: '基于 AI 分析你的喜好和预算' },
  { icon: '🗺️', title: '景点地图', description: '可视化展示行程路线和景点位置' },
  { icon: '💰', title: '预算管理', description: '详细分析各项费用，合理规划预算' }
])

const examples = [
  '下周去成都玩3天，预算5000，喜欢美食',
  '周末去北京2日游，想看历史古迹',
  '暑假带孩子去三亚5天，预算8000',
  '春节去哈尔滨5天，看冰雕和雪景',
  '秋天去云南7天，丽江和大理双城记',
  '夏天去青海湖环线，自驾游'
]

async function handleSubmit() {
  if (!query.value.trim()) {
    message.warning('请输入您的旅行需求')
    return
  }

  loading.value = true
  try {
    // 添加提交动画
    const button = document.querySelector('.search-button')
    if (button) {
      button.classList.add('pulse')
    }

    const { data } = await axios.post('/api/plan', { query: query.value })

    // 移除动画
    if (button) {
      button.classList.remove('pulse')
    }

    // 显示成功提示
    message.success('行程规划已生成，正在为您准备详细信息...')

    // 跳转到规划页面
    router.push({ name: 'plan', params: { id: data.task_id } })
  } catch (e: any) {
    message.error('提交失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 页面加载动画
onMounted(() => {
  // 使用 Intersection Observer 实现滚动动画
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in')
      }
    })
  }, { threshold: 0.1 })

  // 观察所有需要动画的元素
  document.querySelectorAll('.feature-item, .feature-card, .stat-item').forEach(el => {
    observer.observe(el)
  })
})
</script>

<style scoped>
/* 容器样式 */
.home-container {
  width: 100%;
  padding: 32px 24px;
}

/* Hero 区域样式 */
.hero-section {
  margin-bottom: 80px;
  padding: 48px 0;
  background: #f0f9ff;
}

.hero-content {
  max-width: 960px;
  margin: 0 auto;
}

.hero-title {
  font-size: 32px;
  margin: 0 0 16px 0;
  font-weight: 600;
  color: #0f172a;
}

.hero-subtitle {
  font-size: 20px;
  color: #334155;
  margin: 0 0 16px 0;
  font-weight: 500;
}

.hero-description {
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 40px;
}

/* 功能展示 */
.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 40px;
}

.feature-item {
  background: #ffffff;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.feature-item:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.feature-icon {
  color: #0ea5e9;
  font-size: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  border-radius: 8px;
  flex-shrink: 0;
}

.feature-content h3 {
  font-size: 16px;
  margin: 0 0 8px 0;
  color: #0f172a;
  font-weight: 500;
}

.feature-content p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

/* 搜索区域样式 */
.search-section {
  margin-bottom: 80px;
}

.search-container {
  text-align: center;
  margin-bottom: 40px;
}

.search-title {
  font-size: 28px;
  margin: 0 0 16px 0;
  color: #0f172a;
  font-weight: 600;
}

.search-subtitle {
  font-size: 18px;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

.search-box {
  background: #ffffff;
  padding: 32px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  max-width: 800px;
  margin: 0 auto;
}

.search-input {
  margin-bottom: 24px;
}

/* 示例标签 */
.examples {
  margin-bottom: 24px;
  text-align: left;
}

.examples-label {
  color: #64748b;
  margin-right: 8px;
  font-size: 14px;
}

.examples-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 16px;
  padding: 6px 16px;
  font-size: 14px;
  border: 1px solid #e2e8f0;
  color: #64748b;
  background: #f8fafc;
}

.example-tag:hover {
  border-color: #0ea5e9;
  color: #0ea5e9;
}

/* 搜索按钮 */
.search-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.search-button:hover {
  background: #0284c7;
  border-color: #0284c7;
}

/* 功能介绍区域 */
.features-section {
  margin-bottom: 80px;
}

.section-title {
  text-align: center;
  font-size: 28px;
  margin: 0 0 40px 0;
  color: #0f172a;
  font-weight: 600;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
}

.feature-card {
  background: #ffffff;
  padding: 32px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  text-align: center;
  transition: all 0.2s ease;
}

.feature-card:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.feature-card-icon {
  color: #0ea5e9;
  font-size: 32px;
  margin-bottom: 16px;
}

.feature-card h3 {
  font-size: 18px;
  margin: 0 0 12px 0;
  color: #0f172a;
  font-weight: 500;
}

.feature-card p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

/* 统计数据区域 */
.stats-section {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 48px 32px;
  text-align: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
}

.stat-item {
  transition: all 0.2s ease;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #0ea5e9;
}

.stat-label {
  font-size: 14px;
  color: #64748b;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .home-container {
    padding: 24px 16px;
  }

  .hero-title {
    font-size: 24px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .section-title {
    font-size: 20px;
  }

  .search-box {
    padding: 24px;
  }

  .features {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .features-grid {
    gap: 24px;
  }

  .feature-item,
  .feature-card {
    padding: 20px;
  }

  .stats-section {
    padding: 32px 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .stat-number {
    font-size: 20px;
  }
}
</style>
