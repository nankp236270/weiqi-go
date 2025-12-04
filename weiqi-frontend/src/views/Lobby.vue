<template>
  <div class="lobby-container">
    <el-container>
      <!-- 页面头部 -->
      <el-header height="60px">
        <div class="header">
          <h2>🎮 围棋对弈 - 游戏大厅</h2>
          <div class="user-info">
            <el-avatar :size="32" style="margin-right: 10px">
              {{ authStore.user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="username">{{ authStore.user?.username }}</span>
            <el-button type="danger" size="small" @click="handleLogout">
              登出
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main>
        <el-row :gutter="20">
          <!-- 左侧：创建游戏 -->
          <el-col :xs="24" :sm="24" :md="8">
            <el-card class="create-game-card">
              <template #header>
                <div class="card-header">
                  <span>🎯 创建新游戏</span>
                </div>
              </template>
              <el-space direction="vertical" style="width: 100%" :size="15">
                <el-button
                  type="primary"
                  size="large"
                  style="width: 100%"
                  :loading="gameStore.loading"
                  @click="createGame(false)"
                >
                  <el-icon style="margin-right: 5px"><User /></el-icon>
                  创建玩家对战
                </el-button>
                <el-button
                  type="success"
                  size="large"
                  style="width: 100%"
                  :loading="gameStore.loading"
                  @click="createGame(true)"
                >
                  <el-icon style="margin-right: 5px"><Cpu /></el-icon>
                  创建 AI 对战
                </el-button>
              </el-space>
            </el-card>

            <!-- 统计信息 -->
            <el-card class="stats-card" style="margin-top: 20px">
              <template #header>
                <div class="card-header">
                  <span>📊 游戏统计</span>
                </div>
              </template>
              <div class="stats">
                <div class="stat-item">
                  <div class="stat-label">我的游戏</div>
                  <div class="stat-value">{{ myGames.length }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">等待中</div>
                  <div class="stat-value">{{ waitingGames.length }}</div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 中间：我的游戏 -->
          <el-col :xs="24" :sm="24" :md="8">
            <el-card class="game-list-card">
              <template #header>
                <div class="card-header">
                  <span>🎮 我的游戏</span>
                  <el-button
                    size="small"
                    :icon="Refresh"
                    @click="loadMyGames"
                    :loading="loadingMyGames"
                  >
                    刷新
                  </el-button>
                </div>
              </template>
              <div class="game-list">
                <el-empty
                  v-if="myGames.length === 0"
                  description="暂无游戏"
                  :image-size="80"
                />
                <div
                  v-for="game in myGames"
                  :key="game.id"
                  class="game-item"
                  @click="enterGame(game.id)"
                >
                  <div class="game-info">
                    <div class="game-id">
                      游戏 #{{ game.id.slice(0, 8) }}
                    </div>
                    <div class="game-status">
                      <el-tag
                        :type="getStatusType(game.status)"
                        size="small"
                      >
                        {{ getStatusText(game.status) }}
                      </el-tag>
                      <el-tag
                        v-if="game.is_ai_game"
                        type="success"
                        size="small"
                        style="margin-left: 5px"
                      >
                        AI
                      </el-tag>
                    </div>
                  </div>
                  <el-icon class="game-arrow"><ArrowRight /></el-icon>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：等待中的游戏 -->
          <el-col :xs="24" :sm="24" :md="8">
            <el-card class="game-list-card">
              <template #header>
                <div class="card-header">
                  <span>⏳ 等待中的游戏</span>
                  <el-button
                    size="small"
                    :icon="Refresh"
                    @click="loadWaitingGames"
                    :loading="loadingWaitingGames"
                  >
                    刷新
                  </el-button>
                </div>
              </template>
              <div class="game-list">
                <el-empty
                  v-if="waitingGames.length === 0"
                  description="暂无等待中的游戏"
                  :image-size="80"
                />
                <div
                  v-for="game in waitingGames"
                  :key="game.id"
                  class="game-item"
                  @click="joinGame(game.id)"
                >
                  <div class="game-info">
                    <div class="game-id">
                      游戏 #{{ game.id.slice(0, 8) }}
                    </div>
                    <div class="game-status">
                      <el-tag type="warning" size="small">
                        等待玩家
                      </el-tag>
                    </div>
                  </div>
                  <el-icon class="game-arrow"><ArrowRight /></el-icon>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Cpu, Refresh, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useGameStore } from '@/stores/game'
import { gameAPI } from '@/api/game'
import type { Game } from '@/types/game'

const router = useRouter()
const authStore = useAuthStore()
const gameStore = useGameStore()

const myGames = ref<Game[]>([])
const waitingGames = ref<Game[]>([])
const loadingMyGames = ref(false)
const loadingWaitingGames = ref(false)
const autoRefreshTimer = ref<number | null>(null)

// 创建游戏
const createGame = async (isAI: boolean) => {
  try {
    const gameId = await gameStore.createGame(isAI)
    ElMessage.success(isAI ? 'AI 对战创建成功' : '玩家对战创建成功')
    router.push(`/game/${gameId}`)
  } catch (error: any) {
    console.error('Create game error:', error)
    ElMessage.error(error.response?.data?.error || '创建游戏失败')
  }
}

// 静默加载我的游戏（用于自动刷新）
const silentLoadMyGames = async () => {
  try {
    myGames.value = await gameAPI.myGames()
  } catch (error: any) {
    console.error('Silent load my games error:', error)
  }
}

// 静默加载等待中的游戏（用于自动刷新）
const silentLoadWaitingGames = async () => {
  try {
    waitingGames.value = await gameAPI.waitingGames()
  } catch (error: any) {
    console.error('Silent load waiting games error:', error)
  }
}

// 加载我的游戏（手动刷新，显示 loading）
const loadMyGames = async () => {
  loadingMyGames.value = true
  try {
    await silentLoadMyGames()
  } catch (error: any) {
    ElMessage.error('加载游戏列表失败')
  } finally {
    loadingMyGames.value = false
  }
}

// 加载等待中的游戏（手动刷新，显示 loading）
const loadWaitingGames = async () => {
  loadingWaitingGames.value = true
  try {
    await silentLoadWaitingGames()
  } catch (error: any) {
    ElMessage.error('加载等待列表失败')
  } finally {
    loadingWaitingGames.value = false
  }
}

// 进入游戏
const enterGame = (gameId: string) => {
  router.push(`/game/${gameId}`)
}

// 加入游戏
const joinGame = async (gameId: string) => {
  try {
    await gameStore.joinGame(gameId)
    ElMessage.success('加入游戏成功')
    router.push(`/game/${gameId}`)
  } catch (error: any) {
    console.error('Join game error:', error)
    ElMessage.error(error.response?.data?.error || '加入游戏失败')
  }
}

// 登出
const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已登出')
  router.push('/login')
}

// 获取状态类型
const getStatusType = (state: string) => {
  switch (state) {
    case 'waiting':
      return 'warning'
    case 'playing':
      return 'primary'
    case 'finished':
      return 'info'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (state: string) => {
  switch (state) {
    case 'waiting':
      return '等待中'
    case 'playing':
      return '进行中'
    case 'finished':
      return '已结束'
    default:
      return '未知'
  }
}

// 静默刷新所有数据
const silentRefreshAll = async () => {
  await Promise.all([silentLoadMyGames(), silentLoadWaitingGames()])
}

// 启动自动刷新
const startAutoRefresh = () => {
  // 每 3 秒刷新一次，检测对手加入和游戏状态变化
  autoRefreshTimer.value = window.setInterval(() => {
    silentRefreshAll()
  }, 3000)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
    autoRefreshTimer.value = null
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  authStore.initUser()
  await Promise.all([loadMyGames(), loadWaitingGames()])
  // 启动自动刷新
  startAutoRefresh()
})

onUnmounted(() => {
  // 清理定时器
  stopAutoRefresh()
})
</script>

<style scoped>
.lobby-container {
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

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.username {
  font-weight: 500;
  color: #606266;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.create-game-card,
.stats-card,
.game-list-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stats {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.game-list {
  max-height: 500px;
  overflow-y: auto;
}

.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  margin-bottom: 10px;
  background-color: #f9fafc;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.game-item:hover {
  background-color: #ecf5ff;
  transform: translateX(5px);
}

.game-item:last-child {
  margin-bottom: 0;
}

.game-info {
  flex: 1;
}

.game-id {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.game-status {
  display: flex;
  gap: 5px;
}

.game-arrow {
  font-size: 20px;
  color: #c0c4cc;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header h2 {
    font-size: 16px;
  }

  .username {
    display: none;
  }
}
</style>

