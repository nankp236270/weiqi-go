import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User } from '@/types/user'
import { authAPI } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  // 登录
  const login = async (username: string, password: string) => {
    const response = await authAPI.login({ username, password })
    token.value = response.token
    localStorage.setItem('token', response.token)
    
    // 获取用户信息
    await fetchUser()
  }

  // 注册
  const register = async (username: string, email: string, password: string) => {
    await authAPI.register({ username, email, password })
  }

  // 获取用户信息
  const fetchUser = async () => {
    try {
      user.value = await authAPI.me()
      localStorage.setItem('user', JSON.stringify(user.value))
    } catch (error) {
      console.error('Failed to fetch user:', error)
    }
  }

  // 登出
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // 初始化时从 localStorage 恢复用户信息
  const initUser = () => {
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('Failed to parse saved user:', error)
      }
    }
  }

  return {
    user,
    token,
    login,
    register,
    fetchUser,
    logout,
    initUser
  }
})

