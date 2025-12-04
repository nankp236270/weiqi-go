<template>
  <div class="board-container">
    <canvas
      ref="canvasRef"
      :width="canvasSize"
      :height="canvasSize"
      @click="handleClick"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import type { Board as BoardType, Point } from '@/types/game'

interface Props {
  board: BoardType
  disabled?: boolean
  lastMove?: Point | null
  nextPlayer?: 'Black' | 'White'
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  lastMove: null,
  nextPlayer: 'Black'
})

const emit = defineEmits<{
  move: [point: Point]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const hoverPoint = ref<Point | null>(null)

// 棋盘配置
const BOARD_SIZE = 19
const CELL_SIZE = 30
const PADDING = 40
const canvasSize = computed(() => CELL_SIZE * (BOARD_SIZE - 1) + PADDING * 2)

// 星位坐标（19路棋盘）
const STAR_POINTS = [
  { x: 3, y: 3 }, { x: 3, y: 9 }, { x: 3, y: 15 },
  { x: 9, y: 3 }, { x: 9, y: 9 }, { x: 9, y: 15 },
  { x: 15, y: 3 }, { x: 15, y: 9 }, { x: 15, y: 15 }
]

// 绘制棋盘
const drawBoard = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.clearRect(0, 0, canvasSize.value, canvasSize.value)

  // 绘制背景
  ctx.fillStyle = '#DCB35C'
  ctx.fillRect(0, 0, canvasSize.value, canvasSize.value)

  // 绘制网格线
  ctx.strokeStyle = '#000000'
  ctx.lineWidth = 1

  for (let i = 0; i < BOARD_SIZE; i++) {
    const pos = PADDING + i * CELL_SIZE

    // 垂直线
    ctx.beginPath()
    ctx.moveTo(pos, PADDING)
    ctx.lineTo(pos, canvasSize.value - PADDING)
    ctx.stroke()

    // 水平线
    ctx.beginPath()
    ctx.moveTo(PADDING, pos)
    ctx.lineTo(canvasSize.value - PADDING, pos)
    ctx.stroke()
  }

  // 绘制星位
  ctx.fillStyle = '#000000'
  STAR_POINTS.forEach(point => {
    const x = PADDING + point.x * CELL_SIZE
    const y = PADDING + point.y * CELL_SIZE
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })

  // 绘制坐标标签（可选）
  ctx.fillStyle = '#666666'
  ctx.font = '12px Arial'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  // 绘制列标签 (A-T，跳过I)
  const colLabels = 'ABCDEFGHJKLMNOPQRST'
  for (let i = 0; i < BOARD_SIZE; i++) {
    const x = PADDING + i * CELL_SIZE
    ctx.fillText(colLabels[i], x, PADDING - 20)
    ctx.fillText(colLabels[i], x, canvasSize.value - PADDING + 20)
  }

  // 绘制行标签 (1-19)
  for (let i = 0; i < BOARD_SIZE; i++) {
    const y = PADDING + i * CELL_SIZE
    const label = String(BOARD_SIZE - i)
    ctx.fillText(label, PADDING - 20, y)
    ctx.fillText(label, canvasSize.value - PADDING + 20, y)
  }
}

// 绘制棋子
const drawStones = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  if (!props.board || !props.board.grid) return

  const grid = props.board.grid

  for (let y = 0; y < BOARD_SIZE; y++) {
    for (let x = 0; x < BOARD_SIZE; x++) {
      const stone = grid[y][x]
      if (stone === 0) continue

      const canvasX = PADDING + x * CELL_SIZE
      const canvasY = PADDING + y * CELL_SIZE
      const radius = CELL_SIZE * 0.45

      // 绘制棋子阴影
      ctx.shadowColor = 'rgba(0, 0, 0, 0.3)'
      ctx.shadowBlur = 5
      ctx.shadowOffsetX = 2
      ctx.shadowOffsetY = 2

      // 绘制棋子
      ctx.beginPath()
      ctx.arc(canvasX, canvasY, radius, 0, 2 * Math.PI)
      
      if (stone === 1) {
        // 黑子
        ctx.fillStyle = '#000000'
      } else {
        // 白子
        ctx.fillStyle = '#FFFFFF'
      }
      
      ctx.fill()
      
      // 棋子边框
      ctx.shadowColor = 'transparent'
      ctx.strokeStyle = stone === 1 ? '#000000' : '#CCCCCC'
      ctx.lineWidth = 1
      ctx.stroke()
    }
  }
}

// 绘制上一手标记
const drawLastMove = () => {
  if (!props.lastMove) return

  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const x = PADDING + props.lastMove.x * CELL_SIZE
  const y = PADDING + props.lastMove.y * CELL_SIZE
  const radius = CELL_SIZE * 0.2

  ctx.shadowColor = 'transparent'
  ctx.strokeStyle = '#FF0000'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, 2 * Math.PI)
  ctx.stroke()
}

// 绘制悬停提示
const drawHover = () => {
  if (!hoverPoint.value || props.disabled) return

  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const x = PADDING + hoverPoint.value.x * CELL_SIZE
  const y = PADDING + hoverPoint.value.y * CELL_SIZE
  const radius = CELL_SIZE * 0.45

  ctx.shadowColor = 'transparent'
  // 根据当前玩家显示不同颜色的预览
  if (props.nextPlayer === 'Black') {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'  // 黑色预览
  } else {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'  // 白色预览
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)'  // 白色预览需要边框
  }
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, 2 * Math.PI)
  ctx.fill()
  
  // 白色预览添加边框
  if (props.nextPlayer === 'White') {
    ctx.lineWidth = 1
    ctx.stroke()
  }
}

// 完整重绘
const redraw = () => {
  drawBoard()
  drawStones()
  drawLastMove()
  drawHover()
}

// 将画布坐标转换为棋盘坐标
const canvasToBoard = (canvasX: number, canvasY: number): Point | null => {
  const x = Math.round((canvasX - PADDING) / CELL_SIZE)
  const y = Math.round((canvasY - PADDING) / CELL_SIZE)

  if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) {
    return null
  }

  return { x, y }
}

// 处理点击事件
const handleClick = (event: MouseEvent) => {
  if (props.disabled) return

  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const canvasX = event.clientX - rect.left
  const canvasY = event.clientY - rect.top

  const point = canvasToBoard(canvasX, canvasY)
  if (!point) return

  // 检查该位置是否已有棋子
  if (props.board?.grid[point.y][point.x] !== 0) return

  emit('move', point)
}

// 处理鼠标移动
const handleMouseMove = (event: MouseEvent) => {
  if (props.disabled) return

  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const canvasX = event.clientX - rect.left
  const canvasY = event.clientY - rect.top

  const point = canvasToBoard(canvasX, canvasY)
  
  if (point && props.board?.grid[point.y][point.x] === 0) {
    hoverPoint.value = point
  } else {
    hoverPoint.value = null
  }

  redraw()
}

// 处理鼠标离开
const handleMouseLeave = () => {
  hoverPoint.value = null
  redraw()
}

// 监听棋盘变化
watch(() => props.board, () => {
  redraw()
}, { deep: true })

watch(() => props.lastMove, () => {
  redraw()
}, { deep: true })

// 组件挂载时初始化
onMounted(() => {
  redraw()
})
</script>

<style scoped>
.board-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

canvas {
  cursor: pointer;
  border-radius: 4px;
}

canvas:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}
</style>

