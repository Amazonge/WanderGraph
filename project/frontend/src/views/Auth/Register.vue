<template>
  <div class="auth-container">
    <a-card class="auth-card">
      <template #title>
        <div class="auth-title">
          <h2>创建账户</h2>
          <p>加入 WanderGraph，开始您的旅行规划</p>
        </div>
      </template>

      <a-form
        :model="formState"
        @finish="handleFinish"
        @finishFailed="handleFinishFailed"
        layout="vertical"
      >
        <a-form-item
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="用户名"
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          name="email"
          :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]"
        >
          <a-input
            v-model:value="formState.email"
            placeholder="邮箱地址"
            size="large"
          >
            <template #prefix>
              <MailOutlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          name="password"
          :rules="[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少 6 个字符' }
          ]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item
          name="confirmPassword"
          :rules="[
            { required: true, message: '请确认密码' },
            { validator: validatePassword }
          ]"
        >
          <a-input-password
            v-model:value="formState.confirmPassword"
            placeholder="确认密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="agreeTerms">
            我同意 <a href="#">服务条款</a> 和 <a href="#">隐私政策</a>
          </a-checkbox>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            class="register-button"
            size="large"
            :loading="loading"
            block
            :disabled="!agreeTerms"
          >
            注册
          </a-button>
        </a-form-item>

        <div class="auth-divider">
          <span>或</span>
        </div>

        <a-button
          class="social-button"
          size="large"
          block
        >
          <GoogleOutlined />
          使用 Google 注册
        </a-button>

        <div class="login-link">
          已有账号？
          <a href="/login">立即登录</a>
        </div>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { UserOutlined, LockOutlined, MailOutlined, GoogleOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const agreeTerms = ref(false)
const formState = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePassword = (rule: any, value: string) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }
  if (value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const handleFinish = async (values: any) => {
  loading.value = true
  try {
    const success = await userStore.register(values.username, values.email, values.password)
    if (success) {
      router.push('/login')
    }
  } finally {
    loading.value = false
  }
}

const handleFinishFailed = (errorInfo: any) => {
  console.log('Failed:', errorInfo)
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 64px);
  background: #f1f5f9;
  padding: 32px 24px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.auth-title {
  text-align: center;
  margin-bottom: 24px;
}

.auth-title h2 {
  color: #0f172a;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.auth-title p {
  color: #64748b;
  margin: 0;
  font-size: 14px;
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
}

.auth-divider span {
  flex: 1;
  height: 1px;
  background: #e2e8f0;
  margin: 0 16px;
  color: #e2e8f0;
}

.social-button {
  margin-top: 12px;
  background: #fff;
  color: #334155;
}

.social-button:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.login-link {
  text-align: center;
  margin-top: 16px;
  color: #64748b;
}

.login-link a {
  color: #0ea5e9;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>