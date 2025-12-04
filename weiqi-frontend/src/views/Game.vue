<template>
  <div class="game-container">
    <el-container>
      <!-- 页面头部 -->
      <el-header height="60px">
        <div class="header">
          <el-button @click="goBack" :icon="ArrowLeft">
            返回大厅
          </el-button>
          <h2>🎮 游戏对战</h2>
          <div style="width: 100px"></div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main v-loading="gameStore.loading">
        <div v-if="gameStore.currentGame" class="game-content">
          <el-row :gutter="20">
            <!-- 左侧：棋盘 -->
            <el-col :xs="24" :sm="24" :md="16" :lg="16">
              <Board
                :board="gameStore.currentGame.board"
                :disabled="!canMove"
                :last-move="lastMove"
                :next-player="gameStore.currentGame.next_player"
                @move="handleMove"
              />
            </el-col>

            <!-- 右侧：游戏信息和控制 -->
            <el-col :xs="24" :sm="24" :md="8" :lg="8">
              <!-- 玩家信息 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>👥 玩家信息</span>
                  </div>
                </template>
                <div class="players-info">
                  <!-- 黑棋玩家 -->
                  <div class="player-item" :class="{ active: isCurrentPlayer('Black') }">
                    <div class="player-stone black-stone"></div>
                    <div class="player-details">
                      <div class="player-name">
                        黑棋
                        <el-tag v-if="isMe('black')" type="primary" size="small">
                          我
                        </el-tag>
                      </div>
                      <div class="player-captures">
                        提子: {{ gameStore.currentGame.captures_by_b }}
                      </div>
                      <div class="player-time" :class="{ 'time-warning': localBlackTime < 60 }">
                        ⏱️ {{ formatTime(localBlackTime) }}
                      </div>
                    </div>
                  </div>

                  <!-- 白棋玩家 -->
                  <div class="player-item" :class="{ active: isCurrentPlayer('White') }">
                    <div class="player-stone white-stone"></div>
                    <div class="player-details">
                      <div class="player-name">
                        白棋
                        <el-tag v-if="isMe('white')" type="primary" size="small">
                          我
                        </el-tag>
                        <el-tag v-if="gameStore.currentGame.is_ai_game" type="success" size="small">
                          AI
                        </el-tag>
                      </div>
                      <div class="player-captures">
                        提子: {{ gameStore.currentGame.captures_by_w }}
                      </div>
                      <div class="player-time" :class="{ 'time-warning': localWhiteTime < 60 }">
                        ⏱️ {{ formatTime(localWhiteTime) }}
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>

              <!-- 游戏状态 -->
              <el-card class="info-card" style="margin-top: 20px">
                <template #header>
                  <div class="card-header">
                    <span>📊 游戏状态</span>
                  </div>
                </template>
                <div class="game-status">
                  <div class="status-item">
                    <span class="status-label">当前回合:</span>
                    <el-tag :type="getCurrentPlayerType()">
                      {{ getCurrentPlayerText() }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <span class="status-label">游戏状态:</span>
                    <el-tag :type="getGameStateType()">
                      {{ getGameStateText() }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <span class="status-label">连续虚手:</span>
                    <span class="status-value">{{ gameStore.currentGame.passes }}</span>
                  </div>
                </div>
              </el-card>

              <!-- 操作按钮 -->
              <el-card class="info-card" style="margin-top: 20px">
                <template #header>
                  <div class="card-header">
                    <span>🎮 操作</span>
                  </div>
                </template>
                <el-space direction="vertical" style="width: 100%" :size="15">
                  <el-button
                    type="warning"
                    size="large"
                    style="width: 100%"
                    :disabled="!canMove"
                    :loading="gameStore.loading"
                    @click="handlePass"
                  >
                    <el-icon style="margin-right: 5px"><CircleClose /></el-icon>
                    虚手 (Pass)
                  </el-button>

                  <!-- 人机对战：投降按钮 -->
                  <el-button
                    v-if="gameStore.currentGame.is_ai_game"
                    type="danger"
                    size="large"
                    style="width: 100%"
                    :disabled="gameStore.currentGame.game_over"
                    @click="handleResign"
                  >
                    <el-icon style="margin-right: 5px"><Close /></el-icon>
                    认输
                  </el-button>

                  <!-- 玩家对战：刷新按钮 -->
                  <el-button
                    v-if="!gameStore.currentGame.is_ai_game"
                    type="info"
                    size="large"
                    style="width: 100%"
                    :loading="refreshing"
                    @click="refreshGame"
                  >
                    <el-icon style="margin-right: 5px"><Refresh /></el-icon>
                    刷新状态
                  </el-button>

                  <el-alert
                    v-if="gameStore.currentGame.is_ai_game"
                    type="info"
                    :closable="false"
                  >
                    <template #title>
                      <span style="font-size: 14px">💡 AI（白棋）会在您落子后自动下棋</span>
                    </template>
                  </el-alert>
                </el-space>
              </el-card>

              <!-- 游戏结果 -->
              <el-card
                v-if="gameStore.currentGame.game_over"
                class="info-card result-card"
                style="margin-top: 20px"
              >
                <template #header>
                  <div class="card-header">
                    <span>🏆 游戏结果</span>
                  </div>
                </template>
                <div class="game-result">
                  <el-result
                    icon="success"
                    title="游戏结束"
                    sub-title="双方均已虚手"
                  >
                    <template #extra>
                      <el-button type="primary" @click="goBack">
                        返回大厅
                      </el-button>
                    </template>
                  </el-result>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <!-- 加载状态 -->
        <el-empty
          v-else-if="!gameStore.loading"
          description="游戏不存在或加载失败"
        >
          <el-button type="primary" @click="goBack">返回大厅</el-button>
        </el-empty>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, CircleClose, Cpu, Refresh, Close } from '@element-plus/icons-vue'
import { useGameStore } from '@/stores/game'
import { useAuthStore } from '@/stores/auth'
import Board from '@/components/Board.vue'
import type { Point } from '@/types/game'

const route = useRoute()
const router = useRouter()
const gameStore = useGameStore()
const authStore = useAuthStore()

const gameId = route.params.id as string
const refreshing = ref(false)
const autoRefreshTimer = ref<number | null>(null)
const countdownTimer = ref<number | null>(null)

// 上一手位置（用于标记）
const lastMove = ref<Point | null>(null)

// 本地倒计时
const localBlackTime = ref(0)
const localWhiteTime = ref(0)

// 判断是否是我的回合
const isMyTurn = computed(() => {
  if (!gameStore.currentGame || !authStore.user) return false
  
  const game = gameStore.currentGame
  const userId = authStore.user.id

  if (game.next_player === 'Black') {
    return game.player_black_id === userId
  } else {
    return game.player_white_id === userId
  }
})

// 判断是否可以落子
const canMove = computed(() => {
  if (!gameStore.currentGame) return false
  if (gameStore.currentGame.game_over) return false
  if (gameStore.currentGame.status !== 'playing') return false
  return isMyTurn.value
})

// 判断当前玩家
const isCurrentPlayer = (player: string) => {
  return gameStore.currentGame?.next_player === player
}

// 判断是否是我
const isMe = (color: string) => {
  if (!gameStore.currentGame || !authStore.user) return false
  
  const game = gameStore.currentGame
  const userId = authStore.user.id

  if (color === 'black') {
    return game.player_black_id === userId
  } else {
    return game.player_white_id === userId
  }
}

// 获取当前玩家类型
const getCurrentPlayerType = () => {
  return gameStore.currentGame?.next_player === 'Black' ? 'info' : 'warning'
}

// 获取当前玩家文本
const getCurrentPlayerText = () => {
  return gameStore.currentGame?.next_player === 'Black' ? '黑棋' : '白棋'
}

// 获取游戏状态类型
const getGameStateType = () => {
  const status = gameStore.currentGame?.status
  switch (status) {
    case 'waiting':
      return 'warning'
    case 'playing':
      return 'success'
    case 'finished':
      return 'info'
    default:
      return 'info'
  }
}

// 获取游戏状态文本
const getGameStateText = () => {
  const status = gameStore.currentGame?.status
  switch (status) {
    case 'waiting':
      return '等待玩家'
    case 'playing':
      return '进行中'
    case 'finished':
      return '已结束'
    default:
      return '未知'
  }
}

// 处理落子
const handleMove = async (point: Point) => {
  try {
    await gameStore.playMove(gameId, point)
    lastMove.value = point
    
    // 更新本地时间
    if (gameStore.currentGame) {
      localBlackTime.value = gameStore.currentGame.black_time_left || 0
      localWhiteTime.value = gameStore.currentGame.white_time_left || 0
    }
    
    ElMessage.success('落子成功')
    
    // 如果是 AI 游戏且轮到 AI（白棋），自动触发 AI 落子
    if (gameStore.currentGame?.is_ai_game && 
        gameStore.currentGame?.next_player === 'White') {
      setTimeout(() => {
        handleAIMove()
      }, 800)
    }
  } catch (error: any) {
    console.error('Play move error:', error)
    const errorMsg = error.response?.data?.error || '落子失败'
    ElMessage.error(errorMsg)
  }
}

// 处理虚手
const handlePass = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要虚手吗？连续两次虚手将结束游戏。',
      '确认虚手',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await gameStore.pass(gameId)
    lastMove.value = null
    
    // 更新本地时间
    if (gameStore.currentGame) {
      localBlackTime.value = gameStore.currentGame.black_time_left || 0
      localWhiteTime.value = gameStore.currentGame.white_time_left || 0
    }
    
    ElMessage.success('虚手成功')

    // 检查游戏是否结束
    if (gameStore.currentGame?.game_over) {
      ElMessage.info('游戏已结束')
    } else if (gameStore.currentGame?.is_ai_game && 
               gameStore.currentGame?.next_player === 'White') {
      // 如果是 AI 游戏且轮到 AI，自动触发 AI 落子
      setTimeout(() => {
        handleAIMove()
      }, 800)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Pass error:', error)
      ElMessage.error(error.response?.data?.error || '虚手失败')
    }
  }
}

// 处理 AI 落子
const handleAIMove = async () => {
  try {
    await gameStore.aiMove(gameId)
    ElMessage.success('AI 已落子')
    
    // 更新上一手位置（这里简化处理，实际应该从响应中获取）
    lastMove.value = null
  } catch (error: any) {
    console.error('AI move error:', error)
    ElMessage.error(error.response?.data?.error || 'AI 落子失败')
  }
}

// 处理认输（人机对战）
const handleResign = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要认输吗？认输后游戏将结束。',
      '确认认输',
      {
        confirmButtonText: '确定认输',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 连续虚手两次结束游戏
    await gameStore.pass(gameId)
    await gameStore.pass(gameId)
    
    ElMessage.success('已认输，游戏结束')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Resign error:', error)
      ElMessage.error('认输失败')
    }
  }
}

// 静默刷新游戏状态（用于自动刷新，不显示 loading）
// 静默刷新游戏状态（用于自动刷新，不显示 loading）
const silentRefreshGame = async () => {
  // 使用 store 的静默刷新方法，不会触发 loading 状态
  await gameStore.silentFetchGame(gameId)
  
  // 更新本地时间
  if (gameStore.currentGame) {
    localBlackTime.value = gameStore.currentGame.black_time_left || 0
    localWhiteTime.value = gameStore.currentGame.white_time_left || 0
  }
}

// 手动刷新游戏状态（显示 loading）
const refreshGame = async () => {
  refreshing.value = true
  try {
    await gameStore.fetchGame(gameId)
    
    // 更新本地时间
    if (gameStore.currentGame) {
      localBlackTime.value = gameStore.currentGame.black_time_left || 0
      localWhiteTime.value = gameStore.currentGame.white_time_left || 0
    }
  } catch (error: any) {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 返回大厅
const goBack = () => {
  router.push('/lobby')
}

// 格式化时间（秒 -> MM:SS）
const formatTime = (seconds: number): string => {
  if (!seconds || seconds < 0) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 启动倒计时
const startCountdown = () => {
  countdownTimer.value = window.setInterval(() => {
    if (!gameStore.currentGame || gameStore.currentGame.game_over) {
      return
    }
    
    // 只有游戏进行中才倒计时
    if (gameStore.currentGame.status === 'playing') {
      if (gameStore.currentGame.next_player === 'Black') {
        if (localBlackTime.value > 0) {
          localBlackTime.value--
          if (localBlackTime.value === 0) {
            ElMessage.error('黑棋超时！')
            silentRefreshGame()
          }
        }
      } else {
        if (localWhiteTime.value > 0) {
          localWhiteTime.value--
          if (localWhiteTime.value === 0) {
            ElMessage.error('白棋超时！')
            silentRefreshGame()
          }
        }
      }
    }
  }, 1000)
}

// 停止倒计时
const stopCountdown = () => {
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
    countdownTimer.value = null
  }
}

// 自动刷新游戏状态
const startAutoRefresh = () => {
  // 只在玩家对战时启用自动刷新
  if (!gameStore.currentGame?.is_ai_game) {
    autoRefreshTimer.value = window.setInterval(async () => {
      // 游戏未结束时刷新
      if (!gameStore.currentGame?.game_over) {
        const oldStatus = gameStore.currentGame?.status
        const oldPasses = gameStore.currentGame?.passes || 0
        const oldNextPlayer = gameStore.currentGame?.next_player
        
        await silentRefreshGame() // 使用静默刷新，避免白屏闪烁
        
        // 检测游戏状态变化：从 waiting 变为 playing
        const newStatus = gameStore.currentGame?.status
        if (oldStatus === 'waiting' && newStatus === 'playing') {
          ElMessage.success('对手已加入，游戏开始！')
        }
        
        // 检测对方虚手：虚手次数增加 且 轮到我了
        const newPasses = gameStore.currentGame?.passes || 0
        const newNextPlayer = gameStore.currentGame?.next_player
        if (newPasses > oldPasses && oldNextPlayer !== newNextPlayer && isMyTurn.value) {
          const opponentColor = newNextPlayer === 'Black' ? '白棋' : '黑棋'
          ElMessage.warning(`${opponentColor}选择了虚手！`)
        }
      }
    }, 2000) // 每2秒刷新一次，实现准实时更新
  }
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }
}

// 组件挂载时加载游戏
onMounted(async () => {
  try {
    await gameStore.fetchGame(gameId)
    
    // 初始化本地倒计时
    if (gameStore.currentGame) {
      localBlackTime.value = gameStore.currentGame.black_time_left || 0
      localWhiteTime.value = gameStore.currentGame.white_time_left || 0
    }
    
    // 如果是 AI 游戏且轮到 AI（白棋），自动触发 AI 落子
    if (gameStore.currentGame?.is_ai_game && 
        gameStore.currentGame?.next_player === 'White') {
      setTimeout(() => {
        handleAIMove()
      }, 1000)
    }
    
    startAutoRefresh()
    startCountdown()
  } catch (error: any) {
    console.error('Load game error:', error)
    ElMessage.error('加载游戏失败')
  }
})

// 组件卸载时停止自动刷新和倒计时
onUnmounted(() => {
  stopAutoRefresh()
  stopCountdown()
})
</script>

<style scoped>
.game-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header h2 {
  margin: 0;
  color: #303133;
  font-size: 20px;
}

.game-content {
  max-width: 1400px;
  margin: 0 auto;
}

.info-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: 600;
}

/* 玩家信息 */
.players-info {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.player-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 6px;
  border: 2px solid transparent;
  transition: all 0.3s;
}

.player-item.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.player-stone {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.black-stone {
  background-color: #000000;
}

.white-stone {
  background-color: #FFFFFF;
  border: 1px solid #CCCCCC;
}

.player-details {
  flex: 1;
}

.player-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.player-captures {
  font-size: 14px;
  color: #909399;
}

.player-time {
  font-size: 14px;
  color: #606266;
  margin-top: 5px;
  font-weight: 600;
}

.player-time.time-warning {
  color: #f56c6c;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 游戏状态 */
.game-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f9fafc;
  border-radius: 4px;
}

.status-label {
  font-weight: 500;
  color: #606266;
}

.status-value {
  font-weight: 600;
  color: #303133;
}

/* 游戏结果 */
.result-card {
  border: 2px solid #67c23a;
}

.game-result {
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header h2 {
    font-size: 16px;
  }

  .player-stone {
    width: 30px;
    height: 30px;
  }

  .player-name {
    font-size: 14px;
  }
}
</style>

