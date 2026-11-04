import { defineStore } from 'pinia'

interface User {
  id: string
  username: string
  email: string
  token: string
  isLoggedIn: boolean
}

export const useUserStore = defineStore('user', {
  state: (): User => ({
    id: '',
    username: '',
    email: '',
    token: '',
    isLoggedIn: false
  }),

  getters: {
    isAuthenticated: (state) => state.isLoggedIn,
    currentUser: (state) => ({
      id: state.id,
      username: state.username,
      email: state.email
    })
  },

  actions: {
    login(username: string, password: string): boolean {
      // 模拟登录验证
      if (username && password) {
        // 生成模拟用户数据
        this.id = Math.random().toString(36).substr(2, 9)
        this.username = username
        this.email = `${username}@example.com`
        this.token = `Bearer ${Math.random().toString(36).substr(2, 16)}`
        this.isLoggedIn = true

        // 保存到 localStorage
        localStorage.setItem('user_token', this.token)
        localStorage.setItem('user_data', JSON.stringify({
          id: this.id,
          username: this.username,
          email: this.email
        }))

        return true
      }
      return false
    },

    register(username: string, email: string, password: string): boolean {
      // 模拟注册
      if (username && email && password) {
        this.id = Math.random().toString(36).substr(2, 9)
        this.username = username
        this.email = email
        this.token = `Bearer ${Math.random().toString(36).substr(2, 16)}`
        this.isLoggedIn = true

        // 保存到 localStorage
        localStorage.setItem('user_token', this.token)
        localStorage.setItem('user_data', JSON.stringify({
          id: this.id,
          username: this.username,
          email: this.email
        }))

        return true
      }
      return false
    },

    logout() {
      this.$reset()
      localStorage.removeItem('user_token')
      localStorage.removeItem('user_data')
    },

    loadUser() {
      const token = localStorage.getItem('user_token')
      const userData = localStorage.getItem('user_data')

      if (token && userData) {
        const data = JSON.parse(userData)
        this.id = data.id
        this.username = data.username
        this.email = data.email
        this.token = token
        this.isLoggedIn = true
      }
    }
  }
})