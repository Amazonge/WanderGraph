<template>
  <div class="plan-container">
    <!-- 顶部操作栏 -->
    <div class="plan-header">
      <div class="header-left">
        <a-button
          type="text"
          class="back-button"
          @click="$router.push('/')"
        >
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          返回首页
        </a-button>
      </div>
      <div class="header-right" v-if="planResult">
        <a-button
          type="primary"
          ghost
          class="export-button"
          @click="handleExportJSON"
        >
          <template #icon>
            <FileTextOutlined />
          </template>
          导出JSON
        </a-button>
        <a-button
          type="primary"
          class="export-button"
          @click="handleExportPNG"
        >
          <template #icon>
            <PictureOutlined />
          </template>
          导出图片
        </a-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="plan-content">
      <!-- Agent 执行进度 -->
      <div class="progress-section">
        <ProgressSteps />
      </div>

      <!-- 行程结果 -->
      <transition name="fade">
        <div v-if="planResult" class="plan-result">
          <!-- Hero Banner -->
          <div class="hero-banner">
            <div class="hero-content">
              <h1 class="banner-title">
                {{ planResult.destination }}
              </h1>
              <p class="banner-subtitle">
                {{ planResult.travel_dates?.start }} ~ {{ planResult.travel_dates?.end }}
                <span class="divider">|</span>
                {{ planResult.traveler_count }} 人旅行
              </p>
            </div>
          </div>

          <!-- 旅行概览卡片 -->
          <div class="overview-cards">
            <a-card class="overview-card">
              <template #title>
                <div class="card-title">
                  <span>旅行概览</span>
                  <a-tag v-if="planResult.budget" color="blue">
                    预算: ¥{{ planResult.budget }}
                  </a-tag>
                </div>
              </template>
              <a-descriptions :column="3" class="overview-descriptions">
                <a-descriptions-item label="目的地">
                  <span class="highlight">{{ planResult.destination }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="出行日期">
                  {{ planResult.travel_dates?.start }} ~ {{ planResult.travel_dates?.end }}
                </a-descriptions-item>
                <a-descriptions-item label="出行人数">
                  <span class="highlight">{{ planResult.traveler_count }} 人</span>
                </a-descriptions-item>
                <a-descriptions-item label="总预算" :span="3">
                  <span class="budget-highlight">¥{{ planResult.budget || '不限' }}</span>
                </a-descriptions-item>
              </a-descriptions>
              <p v-if="planResult.summary" class="plan-summary">
                {{ planResult.summary }}
              </p>
            </a-card>
          </div>

          <!-- 景点地图 -->
          <div v-if="mapAttractions.length" class="map-section">
            <a-card class="map-card">
              <template #title>
                <div class="card-title">
                  <span>景点地图</span>
                  <a-tag color="processing">
                    {{ mapAttractions.length }} 个景点
                  </a-tag>
                </div>
              </template>
              <div class="map-container">
                <AmapContainer :attractions="mapAttractions" height="500px" />
              </div>
            </a-card>
          </div>

          <!-- 逐日行程 -->
          <div class="itinerary-section">
            <h2 class="section-title">
              <span>逐日行程</span>
              <span class="section-subtitle">精心规划的每一天</span>
            </h2>
            <div class="days-container">
              <transition-group name="slide">
                <a-card
                  v-for="day in planResult.itinerary"
                  :key="day.day"
                  class="day-card"
                >
                  <template #title>
                    <div class="day-header">
                      <h3 class="day-title">
                        Day {{ day.day }}
                        <span class="day-date">{{ day.date }}</span>
                      </h3>
                      <div class="day-meta">
                        <a-tag color="blue">{{ day.theme }}</a-tag>
                        <a-tag v-if="day.weather_note" color="orange">
                          {{ day.weather_note }}
                        </a-tag>
                      </div>
                    </div>
                  </template>

                  <div class="timeline-wrapper">
                    <a-timeline>
                      <!-- 活动时间线 -->
                      <a-timeline-item
                        v-for="(act, idx) in day.activities"
                        :key="'act-' + idx"
                        color="blue"
                        class="timeline-activity"
                      >
                        <div class="timeline-content">
                          <div class="activity-header">
                            <span class="activity-time">{{ act.time }}</span>
                            <span class="activity-name">{{ act.name }}</span>
                          </div>
                          <p class="activity-description">{{ act.description }}</p>
                          <div class="activity-details">
                            <span v-if="act.ticket_price" class="detail-item">
                              <span class="detail-label">门票:</span>
                              <span class="detail-value">¥{{ act.ticket_price }}</span>
                            </span>
                            <span v-if="act.duration_hours" class="detail-item">
                              <span class="detail-label">时长:</span>
                              <span class="detail-value">{{ act.duration_hours }}h</span>
                            </span>
                            <span v-if="act.transport_to_next" class="detail-item transport">
                              <span class="detail-label">交通:</span>
                              <span class="detail-value">{{ act.transport_to_next }}</span>
                            </span>
                          </div>
                        </div>
                      </a-timeline-item>

                      <!-- 用餐时间线 -->
                      <a-timeline-item
                        v-for="meal in day.meals"
                        :key="'meal-' + meal.type"
                        color="green"
                        class="timeline-meal"
                      >
                        <div class="timeline-content">
                          <div class="meal-header">
                            <span class="meal-time">{{ meal.time }}</span>
                            <span class="meal-type">{{ mealTypeLabel(meal.type) }}</span>
                          </div>
                          <div class="meal-info">
                            <span class="restaurant">{{ meal.restaurant }}</span>
                            <span v-if="meal.dishes.length" class="dishes">
                              — {{ meal.dishes.join('、') }}
                            </span>
                            <span v-if="meal.estimated_cost" class="meal-cost">
                              ¥{{ meal.estimated_cost }}
                            </span>
                          </div>
                        </div>
                      </a-timeline-item>
                    </a-timeline>
                  </div>

                  <!-- 小贴士 -->
                  <div v-if="day.tips?.length" class="tips-section">
                    <div class="tips-icon"><BulbOutlined /></div>
                    <div class="tips-content">
                      <div v-for="(tip, i) in day.tips" :key="i" class="tip-item">
                        {{ tip }}
                      </div>
                    </div>
                  </div>

                  <!-- 住宿信息 -->
                  <div class="accommodation-section">
                    <div class="accommodation-header">
                      <span class="accommodation-icon"><HomeOutlined /></span>
                      <span class="accommodation-label">住宿</span>
                    </div>
                    <div class="accommodation-content">
                      <span class="accommodation-name">{{ day.accommodation || '待定' }}</span>
                      <span v-if="day.daily_budget_estimate" class="accommodation-cost">
                        预估 ¥{{ day.daily_budget_estimate }}
                      </span>
                    </div>
                  </div>
                </a-card>
              </transition-group>
            </div>
          </div>

          <!-- 美食推荐 -->
          <div v-if="planResult.food_plan?.must_try_dishes?.length" class="food-section">
            <a-card class="food-card">
              <template #title>
                <div class="card-title">
                  <span>必吃美食</span>
                  <a-tag color="red">
                    {{ planResult.food_plan.must_try_dishes.length }} 道推荐
                  </a-tag>
                </div>
              </template>
              <div class="food-grid">
                <div
                  v-for="dish in planResult.food_plan.must_try_dishes"
                  :key="dish.name"
                  class="food-item"
                >
                  <div class="food-card">
                    <div class="food-card-header">
                      <h4 class="food-name">{{ dish.name }}</h4>
                      <a-tag
                        v-if="dish.is_local_specialty"
                        color="orange"
                        size="small"
                        class="specialty-tag"
                      >
                        特色
                      </a-tag>
                    </div>
                    <p class="food-description">{{ dish.description }}</p>
                    <p class="food-price">{{ dish.price_range }}</p>
                  </div>
                </div>
              </div>
            </a-card>
          </div>

          <!-- 预算汇总 -->
          <div v-if="planResult.budget_estimate" class="budget-section">
            <a-card class="budget-card">
              <template #title>
                <div class="card-title">
                  <span>预算汇总</span>
                  <a-tag color="green" class="total-budget">
                    总计 ¥{{ planResult.budget_estimate.total }}
                  </a-tag>
                </div>
              </template>
              <div class="budget-breakdown">
                <div class="budget-item">
                  <div class="budget-label">住宿</div>
                  <div class="budget-value">¥{{ planResult.budget_estimate.hotel }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">餐饮</div>
                  <div class="budget-value">¥{{ planResult.budget_estimate.food }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">交通</div>
                  <div class="budget-value">¥{{ planResult.budget_estimate.transport }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">门票</div>
                  <div class="budget-value">¥{{ planResult.budget_estimate.tickets }}</div>
                </div>
                <div class="budget-divider"></div>
                <div class="budget-total">
                  <div class="total-label">总计</div>
                  <div class="total-value">
                    ¥{{ planResult.budget_estimate.total }}
                    <span
                      v-if="planResult.traveler_count > 1"
                      class="per-person"
                    >
                      (人均 ¥{{ planResult.budget_estimate.per_person?.toFixed(0) }})
                    </span>
                  </div>
                </div>
              </div>
            </a-card>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { usePlanStore } from '@/stores/plan'
import type { TravelPlan, AgentStatus } from '@/types/plan'
import AmapContainer from '@/components/map/AmapContainer.vue'
import ProgressSteps from '@/components/ProgressSteps.vue'
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  PictureOutlined,
  BulbOutlined,
  HomeOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const route = useRoute()
const store = usePlanStore()

const taskId = route.params.id as string
const isRunning = ref(true)
// agent 状态统一走 store，这样 <ProgressSteps />（读 store.agentStatuses）
// 才能随 SSE 实时刷新——之前只更新本地 ref，进度组件永远是空的。
const agentStatuses = computed(() => store.agentStatuses)
const planResult = ref<TravelPlan | null>(null)
const currentNode = ref('')
const hasError = ref(false)
let eventSource: EventSource | null = null

// 页面加载时添加平滑滚动
onMounted(() => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

const AGENT_NAMES: Record<string, string> = {
  coordinator: '任务初始化',
  destination_parser: '目的地解析',
  attraction: '景点搜索',
  weather: '天气查询',
  hotel: '酒店推荐',
  food: '美食规划',
  transport: '交通规划',
  budget: '预算估算',
  image: '图片搜索',
  compiler: '行程编排',
  validator: '校验修正',
  summary: '摘要生成',
}

const stepItems = computed(() =>
  Object.entries(AGENT_NAMES).map(([key, label]) => ({
    title: label,
    status: getStepStatus(key),
  })),
)

const completedSteps = computed(
  () => agentStatuses.value.filter((s) => s.status === 'completed').length,
)

const mapAttractions = computed(() => {
  if (!planResult.value?.attractions) return []
  return planResult.value.attractions
    .filter((a: any) => a.location?.lat && a.location?.lng)
    .map((a: any) => ({
      name: a.name,
      lat: a.location.lat,
      lng: a.location.lng,
    }))
})

function getStepStatus(nodeName: string): string {
  const status = agentStatuses.value.find((s) => s.name === nodeName)?.status
  if (status === 'completed') return 'finish'
  if (status === 'failed') return 'error'
  if (status === 'running') return 'process'
  return 'wait'
}

function mealTypeLabel(type: string): string {
  const map: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐' }
  return map[type] || type
}

function connectSSE() {
  store.clearAgentStatuses()
  eventSource = new EventSource(`/api/plan/${taskId}/stream`)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'node_start') {
      currentNode.value = AGENT_NAMES[data.node] || data.node
      store.updateAgentStatus(data.node, 'running', data.timestamp, data.details)
    }

    if (data.type === 'node_complete') {
      store.updateAgentStatus(
        data.node,
        data.status || 'completed',
        data.timestamp,
        data.details,
      )
      if (data.status === 'failed') {
        hasError.value = true
      }
    }

    if (data.type === 'complete') {
      isRunning.value = false
      eventSource?.close()
      fetchResult()
    }

    if (data.type === 'error') {
      isRunning.value = false
      hasError.value = true
      eventSource?.close()
    }
  }

  eventSource.onerror = () => {
    isRunning.value = false
    eventSource?.close()
    fetchResult()
  }
}

async function fetchResult() {
  try {
    const { data } = await axios.get(`/api/plan/${taskId}`)
    if (data.status === 'completed' && data.full_result) {
      planResult.value = data.full_result
      store.saveToHistory({
        id: taskId,
        query: data.full_result.user_query || '',
        destination: data.destination || '',
        date: new Date().toISOString(),
        plan: data.full_result,
      })
    }
  } catch (e) {
    console.error('获取结果失败', e)
  }
}

function handleExportJSON() {
  if (!planResult.value) return
  const blob = new Blob([JSON.stringify(planResult.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `travel-plan-${planResult.value.destination}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function handleExportPNG() {
  const el = document.getElementById('plan-content')
  if (!el) return
  const { default: html2canvas } = await import('html2canvas')
  const canvas = await html2canvas(el, { scale: 2, useCORS: true })
  canvas.toBlob((blob) => {
    if (blob) {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `travel-plan-${planResult.value?.destination || 'plan'}.png`
      a.click()
      URL.revokeObjectURL(url)
    }
  })
}

onMounted(() => {
  connectSSE()
})

onUnmounted(() => {
  eventSource?.close()
})
</script>

<style scoped>
/* 容器样式 */
.plan-container {
  width: 100%;
  padding: 0 24px 32px;
}

/* 顶部操作栏 */
.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 0 8px;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-button {
  font-size: 16px;
  color: #64748b;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  transition: color 0.2s ease;
}

.back-button:hover {
  color: #0ea5e9;
  background: transparent;
}

.header-right {
  display: flex;
  gap: 12px;
}

.export-button {
  border-radius: 8px;
  transition: all 0.2s ease;
}

/* 内容区域 */
.plan-content {
  min-height: 400px;
}

/* 进度区域 */
.progress-section {
  margin-bottom: 32px;
}

/* Hero Banner */
.hero-banner {
  margin-bottom: 40px;
  padding: 40px 0;
  background: #f0f9ff;
  border-radius: 8px;
}

.hero-content {
  text-align: center;
}

.banner-title {
  font-size: 32px;
  margin: 0 0 12px 0;
  font-weight: 600;
  color: #0f172a;
}

.banner-subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0;
}

.divider {
  margin: 0 12px;
  color: #cbd5e1;
}

/* 旅行概览 */
.overview-cards {
  margin-bottom: 32px;
}

.overview-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.overview-descriptions {
  margin-top: 24px;
}

.highlight {
  color: #0ea5e9;
  font-weight: 500;
}

.budget-highlight {
  font-size: 20px;
  color: #0ea5e9;
  font-weight: 600;
}

.plan-summary {
  margin-top: 20px;
  color: #64748b;
  line-height: 1.6;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

/* 地图区域 */
.map-section {
  margin-bottom: 32px;
}

.map-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.map-container {
  border-radius: 8px;
  overflow: hidden;
}

/* 逐日行程 */
.itinerary-section {
  margin-bottom: 40px;
}

.section-title {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 24px;
}

.section-title span:first-child {
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
}

.section-subtitle {
  font-size: 14px;
  color: #64748b;
}

.days-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.day-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.day-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.day-title span:first-child {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.day-date {
  font-size: 14px;
  color: #666;
}

.day-meta {
  display: flex;
  gap: 8px;
}

/* 时间线样式 */
.timeline-wrapper {
  margin-bottom: 16px;
}

.timeline-activity,
.timeline-meal {
  padding-left: 0;
}

.timeline-content {
  padding-left: 24px;
}

.activity-header,
.meal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.activity-time,
.meal-time {
  font-weight: 600;
  color: #0ea5e9;
  font-size: 14px;
}

.activity-name {
  font-weight: 500;
}

.meal-type {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.activity-description {
  color: #666;
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.activity-details {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.detail-label {
  color: #666;
}

.detail-value {
  font-weight: 500;
}

.transport {
  color: #ff9800;
}

.meal-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.restaurant {
  font-weight: 500;
  color: #333;
}

.dishes {
  color: #666;
}

.meal-cost {
  color: #52c41a;
  font-weight: 500;
}

/* 小贴士 */
.tips-section {
  margin-top: 16px;
  padding: 16px;
  background: #f6ffed;
  border-radius: 8px;
  border-left: 4px solid #52c41a;
  display: flex;
  gap: 12px;
}

.tips-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.tips-content {
  flex: 1;
}

.tip-item {
  color: #52c41a;
  font-size: 14px;
  line-height: 1.6;
}

/* 住宿信息 */
.accommodation-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.accommodation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.accommodation-icon {
  font-size: 18px;
}

.accommodation-label {
  color: #666;
  font-size: 14px;
}

.accommodation-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.accommodation-name {
  font-weight: 500;
  color: #333;
}

.accommodation-cost {
  color: #999;
  font-size: 14px;
}

/* 美食推荐 */
.food-section {
  margin-bottom: 40px;
}

.food-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.food-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.food-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  transition: border-color 0.2s ease;
}

.food-card:hover {
  border-color: #cbd5e1;
}

.food-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.food-name {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.specialty-tag {
  margin: 0;
}

.food-description {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin: 0 0 8px 0;
}

.food-price {
  color: #0ea5e9;
  font-size: 14px;
  font-weight: 500;
  margin: 0;
}

/* 预算汇总 */
.budget-section {
  margin-bottom: 40px;
}

.budget-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.total-budget {
  font-size: 14px;
}

.budget-breakdown {
  display: grid;
  gap: 16px;
}

.budget-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.budget-item:hover {
  background: #f1f5f9;
}

.budget-label {
  color: #666;
  font-size: 16px;
}

.budget-value {
  font-weight: 500;
  color: #333;
  font-size: 16px;
}

.budget-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 8px 0;
}

.budget-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
}

.total-label {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.total-value {
  font-size: 24px;
  font-weight: 700;
  color: #0ea5e9;
}

.per-person {
  font-size: 14px;
  font-weight: 400;
  color: #666;
  margin-left: 8px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .plan-container {
    padding: 0 16px;
  }

  .hero-banner {
    padding: 32px;
  }

  .banner-title {
    font-size: 30px;
  }

  .section-title span:first-child {
    font-size: 28px;
  }

  .overview-descriptions {
    :deep(.ant-descriptions-item-label) {
      width: 100px !important;
    }
  }
}

@media (max-width: 768px) {
  .plan-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .hero-banner {
    padding: 24px;
  }

  .banner-title {
    font-size: 28px;
  }

  .banner-subtitle {
    font-size: 16px;
  }

  .overview-descriptions {
    :deep(.ant-descriptions) {
      :deep(.ant-descriptions-item) {
        padding-bottom: 12px;
      }
    }
  }

  .day-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .activity-details {
    flex-direction: column;
    gap: 8px;
  }

  .food-grid {
    grid-template-columns: 1fr;
  }

  .budget-breakdown {
    gap: 12px;
  }

  .budget-item {
    padding: 8px;
  }

  .total-value {
    font-size: 20px;
  }
}

/* 暗色模式适配 */
.dark .hero-banner {
  background: #0f172a;
}

.dark .overview-card,
.dark .map-card,
.dark .day-card,
.dark .food-card,
.dark .budget-card {
  background: #1e293b;
  border-color: #334155;
}

.dark .plan-summary {
  background: #1e293b;
}

.dark .tips-section {
  background: #1e293b;
}

.dark .budget-item {
  background: #1e293b;
}

.dark .budget-item:hover {
  background: #334155;
}

.dark .activity-name,
.dark .restaurant,
.dark .accommodation-name {
  color: #fff;
}

.dark .activity-description,
.dark .food-description {
  color: #ccc;
}
</style>
