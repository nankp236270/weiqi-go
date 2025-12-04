import client from './client'
import type { Game, Point } from '@/types/game'

export const gameAPI = {
  // 创建游戏
  async createGame(data: { is_ai_game: boolean }): Promise<{ game_id: string }> {
    const response = await client.post('/v1/games', data)
    return response.data
  },

  // 获取游戏状态
  async getGame(gameId: string): Promise<Game> {
    const response = await client.get(`/v1/games/${gameId}`)
    return response.data
  },

  // 落子
  async playMove(gameId: string, point: Point): Promise<Game> {
    const response = await client.post(`/v1/games/${gameId}/move`, point)
    return response.data
  },

  // 虚手
  async pass(gameId: string): Promise<Game> {
    const response = await client.post(`/v1/games/${gameId}/pass`)
    return response.data
  },

  // AI 落子
  async aiMove(gameId: string): Promise<Game> {
    const response = await client.post(`/v1/games/${gameId}/ai-move`)
    return response.data
  },

  // 加入游戏
  async joinGame(gameId: string): Promise<Game> {
    const response = await client.post(`/v1/games/${gameId}/join`)
    return response.data
  },

  // 获取我的游戏列表
  async myGames(): Promise<Game[]> {
    const response = await client.get('/v1/games/my')
    return response.data.games || []
  },

  // 获取等待中的游戏列表
  async waitingGames(): Promise<Game[]> {
    const response = await client.get('/v1/games/waiting')
    return response.data.games || []
  }
}
