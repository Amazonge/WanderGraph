<template>
  <div class="progress-container">
    <!-- 顶部进度条 -->
    <div class="progress-header">
      <div class="progress-info">
        <h3 class="progress-title">行程规划进度</h3>
        <div class="progress-stats">
          <span class="stat-item">
            已完成: <strong>{{ completedSteps }}</strong>
          </span>
          <span class="stat-divider">/</span>
          <span class="stat-item">
            总计: <strong>{{ totalSteps }}</strong>
          </span>
          <span class="stat-divider">|</span>
          <span class="progress-percentage">{{ progressPercentage }}%</span>
        </div>
      </div>
      <div class="progress-actions">
        <a-button
          type="text"
          size="small"
          :icon="isExpanded ? 'up' : 'down'"
          @click="toggleExpand"
          class="expand-button"
        >
          {{ isExpanded ? '收起详情' : '展开详情' }}
        </a-button>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-wrapper">
      <div class="progress-bar-track">
        <div
          class="progress-bar-fill"
          :style="{ width: progressPercentage + '%' }"
        >
        </div>
        <div class="progress-bar-label">
          {{ progressPercentage }}%
        </div>
      </div>
      <div class="progress-steps-indicator">
        <div
          v-for="(step, index) in stepItems"
          :key="step.key"
          class="step-indicator"
          :class="getStepIndicatorClass(step, index)"
          @click="scrollToStep(index)"
        >
          <div class="step-dot">
            <div class="step-icon">
              <CheckCircleOutlined v-if="step.status === 'finish'" />
              <CloseCircleOutlined v-else-if="step.status === 'error'" />
              <LoadingOutlined v-else-if="step.status === 'process'" />
              <MinusOutlined v-else />
            </div>
          </div>
          <div class="step-tooltip">
            {{ step.title }}
            <div class="step-status">
              {{ getStatusText(step.status) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 当前执行节点 -->
    <div v-if="isRunning && currentNode" class="current-execution">
      <div class="execution-content">
        <div class="execution-icon">
          <a-spin size="small" />
        </div>
        <div class="execution-text">
          <div class="execution-title">正在执行</div>
          <div class="execution-node">{{ currentNode }}</div>
        </div>
        <div class="execution-time">
          {{ formatExecutionTime }}
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="hasError" class="error-container">
      <a-alert
        type="error"
        :message="errorMessage"
        show-icon
        :description="errorDetails"
        closable
        @close="dismissError"
        class="error-alert"
      />
      <a-button
        type="primary"
        size="small"
        @click="retryFailed"
        class="retry-button"
      >
        重试失败节点
      </a-button>
    </div>

    <!-- 详细进度面板 -->
    <transition name="slide-down">
      <div v-if="isExpanded && detailedProgress" class="detailed-panel">
        <a-card class="details-card">
          <template #title>
            <div class="details-header">
              <span>详细执行状态</span>
              <a-tag color="blue">
                {{ completedSteps }}/{{ totalSteps }} 完成
              </a-tag>
            </div>
          </template>
          <div class="details-content">
            <a-timeline mode="left">
              <a-timeline-item
                v-for="(item, index) in detailedProgress"
                :key="index"
                :color="getItemColor(item.status)"
                class="detail-timeline-item"
              >
                <template #dot>
                  <div class="custom-dot">
                    <a-tag
                      :color="getItemColor(item.status)"
                      size="small"
                    >
                      {{ item.status.toUpperCase() }}
                    </a-tag>
                  </div>
                </template>
                <div class="timeline-content">
                  <div class="node-info">
                    <div class="node-header">
                      <span class="node-name">{{ item.node }}</span>
                      <a-tag :color="getItemColor(item.status)" size="small">
                        {{ getStatusText(item.status) }}
                      </a-tag>
                    </div>
                    <div v-if="item.details" class="node-details">
                      {{ item.details }}
                    </div>
                    <div v-if="item.timestamp" class="node-timestamp">
                      {{ formatTimestamp(item.timestamp) }}
                    </div>
                  </div>
                </div>
              </a-timeline-item>
            </a-timeline>
          </div>
        </a-card>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { usePlanStore } from '@/stores/plan'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  MinusOutlined
} from '@ant-design/icons-vue'

interface ProgressItem {
  node: string
  status: 'running' | 'completed' | 'failed' | 'waiting'
  details?: string
  timestamp?: string
}

const store = usePlanStore()
const isExpanded = ref(false)

// Agent 名称映射
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

// 计算属性
const completedSteps = computed(
  () => store.agentStatuses.filter((s) => s.status === 'completed').length
)

const totalSteps = computed(() => Object.keys(AGENT_NAMES).length)

const progressPercentage = computed(() => {
  if (totalSteps.value === 0) return 0
  return Math.round((completedSteps.value / totalSteps.value) * 100)
})

const hasError = computed(() => store.agentStatuses.some((s) => s.status === 'failed'))

const currentNode = computed(() => {
  const running = store.agentStatuses.find((s) => s.status === 'running')
  return running ? AGENT_NAMES[running.name] || running.name : ''
})

const isRunning = computed(() => store.agentStatuses.some((s) => s.status === 'running'))

// 错误信息
const errorMessage = computed(() => {
  const failed = store.agentStatuses.filter((s) => s.status === 'failed')
  if (failed.length === 1) {
    return `${AGENT_NAMES[failed[0].name]} 节点执行失败`
  }
  return `${failed.length} 个节点执行失败，结果可能不完整`
})

const errorDetails = computed(() => {
  const failed = store.agentStatuses.filter((s) => s.status === 'failed')
  return failed.map(f => `• ${AGENT_NAMES[f.name]}`).join('\n')
})

// 详细进度
const detailedProgress = computed((): ProgressItem[] => {
  return store.agentStatuses.map((status) => ({
    node: status.name,
    status: status.status as 'running' | 'completed' | 'failed' | 'waiting',
    details: status.details,
    timestamp: status.timestamp,
  }))
})

// 步骤项
const stepItems = computed(() =>
  Object.entries(AGENT_NAMES).map(([key, label]) => ({
    key,
    title: label,
    status: getStatus(key),
  }))
)

// 执行时间
const executionStartTime = computed(() => {
  const firstRunning = store.agentStatuses.find(s => s.status === 'running')
  return firstRunning?.timestamp
})

const formatExecutionTime = computed(() => {
  if (!executionStartTime.value) return ''
  const start = new Date(executionStartTime.value)
  const now = new Date()
  const diff = Math.floor((now.getTime() - start.getTime()) / 1000)

  if (diff < 60) return `${diff}秒`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟`
  return `${Math.floor(diff / 3600)}小时${Math.floor((diff % 3600) / 60)}分钟`
})

// 方法
function getStatus(nodeName: string): string {
  const status = store.agentStatuses.find((s) => s.name === nodeName)?.status
  if (status === 'completed') return 'finish'
  if (status === 'failed') return 'error'
  if (status === 'running') return 'process'
  return 'wait'
}

function getItemColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'green'
    case 'failed':
      return 'red'
    case 'running':
      return 'blue'
    default:
      return 'gray'
  }
}

function getStatusText(status: string): string {
  const map: Record<string, string> = {
    completed: '已完成',
    failed: '失败',
    running: '运行中',
    waiting: '等待中'
  }
  return map[status] || status
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

function getStepIndicatorClass(step: any, index: number): string {
  const classes: string[] = []
  if (index < completedSteps.value) classes.push('completed')
  if (step.status === 'error') classes.push('error')
  if (step.status === 'process') classes.push('active')
  if (index === completedSteps.value && step.status === 'process') classes.push('current')
  return classes.join(' ')
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function scrollToStep(index: number) {
  const element = document.querySelectorAll('.step-indicator')[index]
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

function dismissError() {
  store.clearErrors()
}

function retryFailed() {
  store.retryFailedNodes()
}
</script>

<style scoped>
/* 进度容器 */
.progress-container {
  margin-bottom: 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 24px;
}

/* 进度头部 */
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.progress-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.progress-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
}

.stat-item strong {
  color: #0ea5e9;
}

.stat-divider {
  color: #cbd5e1;
}

.progress-percentage {
  font-weight: 600;
  color: #0ea5e9;
}

.progress-actions {
  display: flex;
  align-items: center;
}

.expand-button {
  color: #64748b;
  border: none;
  padding: 4px 12px;
  border-radius: 6px;
  transition: color 0.2s ease;
}

.expand-button:hover {
  color: #0ea5e9;
  background: transparent;
}

/* 进度条 */
.progress-bar-wrapper {
  position: relative;
  margin-bottom: 32px;
}

.progress-bar-track {
  position: relative;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 24px;
}

.progress-bar-fill {
  height: 100%;
  background: #0ea5e9;
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-bar-label {
  position: absolute;
  right: 0;
  top: -20px;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

/* 步骤指示器 */
.progress-steps-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  padding: 0 16px;
}

.step-indicator {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: color 0.2s ease;
  z-index: 2;
}

.step-indicator.completed {
  color: #10b981;
}

.step-indicator.error {
  color: #ef4444;
}

.step-indicator.active {
  color: #0ea5e9;
}

.step-dot {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f1f5f9;
  transition: background 0.2s ease;
  margin-bottom: 8px;
}

.step-indicator.completed .step-dot {
  background: #10b981;
}

.step-indicator.error .step-dot {
  background: #ef4444;
}

.step-indicator.active .step-dot {
  background: #0ea5e9;
}

.step-icon {
  font-size: 16px;
  color: white;
}

.step-tooltip {
  text-align: center;
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.step-status {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}

/* 当前执行状态 */
.current-execution {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  margin-bottom: 16px;
}

.execution-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.execution-icon {
  color: #0ea5e9;
}

.execution-title {
  font-size: 14px;
  color: #64748b;
}

.execution-node {
  font-size: 16px;
  font-weight: 500;
  color: #0ea5e9;
}

.execution-time {
  font-size: 12px;
  color: #94a3b8;
}

/* 错误提示 */
.error-container {
  margin-bottom: 16px;
}

.error-alert {
  margin-bottom: 12px;
}

.retry-button {
  border-radius: 8px;
}

/* 详细面板 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.details-card {
  border-radius: 8px;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-content {
  margin-top: 16px;
}

.detail-timeline-item {
  padding-bottom: 16px !important;
}

.custom-dot {
  background: white;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

.node-info {
  padding-left: 16px;
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.node-name {
  font-weight: 500;
  color: #0f172a;
}

.node-details {
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

.node-timestamp {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .progress-stats {
    flex-wrap: wrap;
    gap: 4px;
  }

  .progress-steps-indicator {
    flex-wrap: wrap;
    gap: 16px;
  }

  .step-indicator {
    flex: 0 0 calc(50% - 8px);
  }

  .current-execution {
    flex-direction: column;
    text-align: center;
  }
}

/* 暗色模式适配 */
.dark .progress-container {
  background: #1e293b;
  border-color: #334155;
}

.dark .progress-bar-track {
  background: #334155;
}

.dark .step-dot {
  background: #334155;
}

.dark .current-execution {
  background: #1e293b;
}

.dark .node-name {
  color: #f1f5f9;
}
</style>