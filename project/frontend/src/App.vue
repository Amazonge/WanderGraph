<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <a-layout-header class="header">
      <div class="header-content">
        <div class="header-left">
          <div class="logo">
            <GlobalOutlined class="logo-icon" />
            <h1 class="logo-text">WanderGraph</h1>
          </div>

          <a-menu
            v-model:selectedKeys="selectedKeys"
            mode="horizontal"
            class="main-menu"
          >
            <a-menu-item key="home" @click="$router.push('/')">
              <template #icon>
                <HomeOutlined />
              </template>
              首页
            </a-menu-item>
            <a-menu-item key="recommendations" @click="$router.push('/recommendations')">
              <template #icon>
                <StarOutlined />
              </template>
              推荐
            </a-menu-item>
            <a-menu-item key="reviews" @click="$router.push('/reviews')">
              <template #icon>
                <CommentOutlined />
              </template>
              评价
            </a-menu-item>
            <a-menu-item key="history" @click="$router.push('/history')">
              <template #icon>
                <HistoryOutlined />
              </template>
              历史记录
            </a-menu-item>
          </a-menu>
        </div>

        <div class="header-right">
          <template v-if="userStore.isAuthenticated">
            <a-dropdown>
              <a-button type="text" class="user-dropdown">
                <template #icon>
                  <UserOutlined />
                </template>
                {{ userStore.currentUser.username }}
                <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="profile" @click="$router.push('/profile')">
                    <template #icon>
                      <SettingOutlined />
                    </template>
                    个人资料
                  </a-menu-item>
                  <a-menu-item key="logout" @click="handleLogout">
                    <template #icon>
                      <LogoutOutlined />
                    </template>
                    退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </template>
          <template v-else>
            <a-button
              type="primary"
              class="auth-btn"
              @click="$router.push('/login')"
            >
              <template #icon>
                <LoginOutlined />
              </template>
              登录
            </a-button>
            <a-button
              class="auth-btn"
              @click="$router.push('/register')"
            >
              <template #icon>
                <UserAddOutlined />
              </template>
              注册
            </a-button>
          </template>

          <!-- 主题切换按钮 -->
          <a-button
            type="text"
            class="theme-toggle"
            @click="toggleTheme"
          >
            <template #icon>
              {{ isDark ? '🌙' : '☀️' }}
            </template>
          </a-button>
        </div>
      </div>
    </a-layout-header>

    <!-- 内容区域 -->
    <div class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import {
  HomeOutlined,
  HistoryOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  LoginOutlined,
  UserAddOutlined,
  DownOutlined,
  StarOutlined,
  CommentOutlined,
  GlobalOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const router = useRouter()
const userStore = useUserStore()
const selectedKeys = ref<string[]>(['home'])
const isDark = ref(false)

// 监听路由变化更新选中状态
router.afterEach((to) => {
  selectedKeys.value = [to.name as string]
})

// 主题切换
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark')

  // 保存主题偏好
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')

  message.success(`已切换到${isDark.value ? '深色' : '浅色'}主题`)
}

onMounted(() => {
  userStore.loadUser()

  // 恢复主题偏好
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
  message.success('已成功退出登录')
}
</script>

<style scoped>
/* 应用容器 */
.app-container {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 48px;
}

/* Logo样式 */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  color: #0ea5e9;
  font-size: 20px;
}

.logo-text {
  color: #0f172a;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

/* 主菜单 */
.main-menu {
  background: transparent !important;
  border: none;
}

.main-menu .ant-menu-item {
  color: #64748b;
  margin: 0 8px;
  font-weight: 400;
}

.main-menu .ant-menu-item:hover {
  background: #f0f9ff !important;
  color: #0ea5e9;
}

.main-menu .ant-menu-item-selected {
  color: #0ea5e9;
  font-weight: 500;
}

/* 用户下拉菜单 */
.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.user-dropdown {
  color: #0f172a;
}

.auth-btn {
  color: #0f172a;
  border-color: #e2e8f0;
  background: transparent;
}

.auth-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0f172a;
}

/* 主题切换按钮 */
.theme-toggle {
  color: #64748b;
  border: 1px solid #e2e8f0;
  background: transparent;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0ea5e9;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding: 32px 24px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .header-content {
    padding: 0 20px;
  }

  .main-content {
    padding: 24px 20px;
  }
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
    height: 56px;
  }

  .header-left {
    gap: 24px;
  }

  .logo-text {
    font-size: 16px;
  }

  .main-menu {
    display: none;
  }

  .main-content {
    padding: 16px;
  }

  .user-dropdown {
    display: none;
  }

  .header-right {
    gap: 12px;
  }
}

@media (max-width: 576px) {
  .header-right {
    gap: 8px;
  }

  .auth-btn {
    display: none;
  }
}
</style>