import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Game, Point } from '@/types/game'
import { gameAPI } from '@/api/game'

export const useGameStore = defineStore('game', () => {
  const currentGame = ref<Game | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 创建游戏
  const createGame = async (isAIGame: boolean) => {
    loading.value = true
    error.value = null
    try {
      const response = await gameAPI.createGame({ is_ai_game: isAIGame })
      return response.game_id
    } catch (err: any) {
      error.value = err.response?.data?.error || '创建游戏失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 静默获取游戏状态（不设置 loading，用于自动刷新）
  const silentFetchGame = async (gameId: string) => {
    try {
      currentGame.value = await gameAPI.getGame(gameId)
    } catch (err: any) {
      // 静默失败，不设置 error，避免打扰用户
      console.error('Silent fetch game error:', err)
    }
  }

  // 获取游戏状态（设置 loading，用于手动刷新）
  const fetchGame = async (gameId: string) => {
    loading.value = true
    error.value = null
    try {
      currentGame.value = await gameAPI.getGame(gameId)
    } catch (err: any) {
      error.value = err.response?.data?.error || '获取游戏失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 加入游戏
  const joinGame = async (gameId: string) => {
    loading.value = true
    error.value = null
    try {
      currentGame.value = await gameAPI.joinGame(gameId)
    } catch (err: any) {
      error.value = err.response?.data?.error || '加入游戏失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 落子
  const playMove = async (gameId: string, point: Point) => {
    loading.value = true
    error.value = null
    try {
      currentGame.value = await gameAPI.playMove(gameId, point)
    } catch (err: any) {
      error.value = err.response?.data?.error || '落子失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 虚手
  const pass = async (gameId: string) => {
    loading.value = true
    error.value = null
    try {
      currentGame.value = await gameAPI.pass(gameId)
    } catch (err: any) {
      error.value = err.response?.data?.error || '虚手失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // AI 落子
  const aiMove = async (gameId: string) => {
    loading.value = true
    error.value = null
    try {
      currentGame.value = await gameAPI.aiMove(gameId)
    } catch (err: any) {
      error.value = err.response?.data?.error || 'AI 落子失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  return {
    currentGame,
    loading,
    error,
    createGame,
    fetchGame,
    silentFetchGame,
    joinGame,
    playMove,
    pass,
    aiMove,
    clearError
  }
})

