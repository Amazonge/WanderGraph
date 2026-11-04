<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">
        <UserOutlined class="title-icon" />
        个人资料
      </h1>
      <p class="page-subtitle">查看你的账户信息与规划记录概览</p>
    </div>

    <a-card class="profile-card" v-if="userStore.isAuthenticated">
      <a-descriptions :column="2" bordered>
        <a-descriptions-item label="用户名">
          {{ userStore.currentUser.username }}
        </a-descriptions-item>
        <a-descriptions-item label="邮箱">
          {{ userStore.currentUser.email }}
        </a-descriptions-item>
        <a-descriptions-item label="用户ID">
          {{ userStore.currentUser.id }}
        </a-descriptions-item>
        <a-descriptions-item label="历史规划数">
          {{ store.history.length }}
        </a-descriptions-item>
      </a-descriptions>

      <div class="profile-actions">
        <a-button type="primary" @click="$router.push('/history')">
          查看历史记录
        </a-button>
        <a-button @click="$router.push('/')">开始新规划</a-button>
        <a-button danger @click="handleLogout">退出登录</a-button>
      </div>
    </a-card>

    <a-empty v-else description="尚未登录">
      <a-button type="primary" @click="$router.push('/login')">去登录</a-button>
    </a-empty>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { usePlanStore } from '@/stores/plan'
import { UserOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const router = useRouter()
const userStore = useUserStore()
const store = usePlanStore()

onMounted(() => {
  userStore.loadUser()
  store.loadHistory()
})

function handleLogout() {
  userStore.logout()
  message.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.profile-page {
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

.profile-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.profile-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 768px) {
  .profile-page {
    padding: 0 16px 24px;
  }
  .page-title {
    font-size: 20px;
  }
  .profile-actions {
    flex-direction: column;
  }
}
</style>
