<template>
  <div class="not-found">
    <div class="content">
      <div class="error-icon"><FrownOutlined /></div>
      <h1>404</h1>
      <h2>页面未找到</h2>
      <p>抱歉，您访问的页面不存在</p>
      <div class="actions">
        <a-button type="primary" @click="goHome">
          <template #icon>
            <HomeOutlined />
          </template>
          返回首页
        </a-button>
        <a-button @click="goBack">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          返回上页
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeOutlined, ArrowLeftOutlined, FrownOutlined } from '@ant-design/icons-vue'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  router.go(-1)
}
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  background: #f8fafc;
  padding: 32px 24px;
}

.content {
  text-align: center;
  padding: 48px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.error-icon {
  font-size: 64px;
  color: #94a3b8;
  margin-bottom: 16px;
}

h1 {
  font-size: 96px;
  color: #0ea5e9;
  margin-bottom: 16px;
  line-height: 1;
  font-weight: 600;
}

h2 {
  font-size: 24px;
  color: #0f172a;
  margin-bottom: 16px;
  font-weight: 600;
}

p {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 32px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
