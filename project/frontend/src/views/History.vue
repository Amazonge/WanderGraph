<template>
  <div class="history-page">
    <div class="page-header">
      <h1 class="page-title">
        <HistoryOutlined class="title-icon" />
        历史规划记录
      </h1>
      <p class="page-subtitle">查看和管理你过往的旅行规划</p>
    </div>

    <a-empty v-if="history.length === 0" description="暂无记录">
      <a-button type="primary" @click="$router.push('/')">去规划</a-button>
    </a-empty>

    <a-card v-else class="history-card" :bordered="false">
      <a-list :data-source="history" item-layout="horizontal">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta>
              <template #title>
                <a class="history-link" @click="$router.push({ name: 'plan', params: { id: item.id } })">
                  {{ item.destination || '旅行计划' }}
                </a>
              </template>
              <template #description>
                <div class="history-query">{{ item.query }}</div>
                <div class="history-date">{{ formatDate(item.date) }}</div>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a-button
                type="link"
                @click="$router.push({ name: 'plan', params: { id: item.id } })"
              >
                查看
              </a-button>
              <a-button type="link" danger @click="handleDelete(item.id)">删除</a-button>
            </template>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePlanStore } from '@/stores/plan'
import { HistoryOutlined } from '@ant-design/icons-vue'

const store = usePlanStore()
store.loadHistory()

const history = computed(() => store.history)

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

function handleDelete(id: string) {
  store.deleteHistory(id)
}
</script>

<style scoped>
.history-page {
  width: 100%;
  padding: 0 24px 32px;
}

.page-header {
  margin-bottom: 24px;
  padding: 24px;
  background: #f0f9ff;
  border-radius: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.title-icon {
  color: #0ea5e9;
  font-size: 24px;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.history-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.history-link {
  color: #0f172a;
  font-weight: 500;
  transition: color 0.2s ease;
}

.history-link:hover {
  color: #0ea5e9;
}

.history-query {
  color: #334155;
  font-size: 14px;
  line-height: 1.5;
}

.history-date {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .history-page {
    padding: 0 16px 24px;
  }

  .page-title {
    font-size: 20px;
  }
}
</style>
