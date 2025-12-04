export interface Point {
  x: number
  y: number
}

export interface Board {
  size: number
  grid: number[][]  // 0=空, 1=黑, 2=白
}

export interface Game {
  id: string
  board: Board
  next_player: 'Black' | 'White'
  passes: number
  game_over: boolean
  captures_by_b: number
  captures_by_w: number
  player_black_id?: string
  player_white_id?: string
  status: 'waiting' | 'playing' | 'finished'
  is_ai_game: boolean
  black_time_left: number
  white_time_left: number
  last_move_time: number
  time_per_player: number
  created_at: string
}

export interface MoveRequest {
  x: number
  y: number
}

export interface GameListItem {
  id: string
  status: string
  player_black_id?: string
  player_white_id?: string
  created_at: string
}

export interface CreateGameRequest {
  is_ai_game: boolean
}

