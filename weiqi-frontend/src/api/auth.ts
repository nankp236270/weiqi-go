import client from './client'
import type { User } from '@/types/user'

export const authAPI = {
  // 用户注册
  async register(data: { username: string; email: string; password: string }) {
    const response = await client.post('/v1/auth/register', data)
    return response.data
  },

  // 用户登录
  async login(data: { username: string; password: string }): Promise<{ token: string }> {
    const response = await client.post('/v1/auth/login', data)
    return response.data
  },

  // 获取当前用户信息
  async me(): Promise<User> {
    const response = await client.get('/v1/auth/me')
    return response.data
  }
}
