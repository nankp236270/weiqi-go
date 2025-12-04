package game

import (
	"errors"
	"time"
)

var (
	ErrKoViolation = errors.New("move violates Ko rule (positional superko")
	ErrTimeOut     = errors.New("player time out")
)

// ScoreResult 包含了计分的详细结果
type ScoreResult struct {
	BlackScore float64 `json:"black_score"`
	WhiteScore float64 `json:"white_score"`
	Winner     Player  `json:"winner"`
}

// GameStatus 表示游戏状态
type GameStatus string

const (
	GameStatusWaiting  GameStatus = "waiting"  // 等待玩家加入
	GameStatusPlaying  GameStatus = "playing"  // 进行中
	GameStatusFinished GameStatus = "finished" // 已结束
)

// Game 结构体管理整个对局的状态
type Game struct {
	Board           *Board          `json:"board" bson:"board"`
	History         map[string]bool `json:"-" bson:"history"` // 存储棋盘状态的哈希，用于 Ko 规则检查 & 使用 json:"-" 来在API响应中隐藏这个字段
	NextPlayer      Player          `json:"next_player" bson:"next_player"`
	Passes          int             `json:"passes" bson:"passes"`
	GameOver        bool            `json:"game_over" bson:"game_over"`
	CapturesByB     int             `json:"captures_by_b" bson:"captures_by_b"`
	CapturesByW     int             `json:"captures_by_w" bson:"captures_by_w"`
	PlayerBlack     string          `json:"player_black_id" bson:"player_black"`     // 黑棋玩家 ID
	PlayerWhite     string          `json:"player_white_id" bson:"player_white"`     // 白棋玩家 ID
	Status          GameStatus      `json:"status" bson:"status"`                    // 游戏状态
	IsAIGame        bool            `json:"is_ai_game" bson:"is_ai_game"`            // 是否为人机对弈
	BlackTimeLeft   int64           `json:"black_time_left" bson:"black_time_left"`  // 黑棋剩余时间（秒）
	WhiteTimeLeft   int64           `json:"white_time_left" bson:"white_time_left"`  // 白棋剩余时间（秒）
	LastMoveTime    int64           `json:"last_move_time" bson:"last_move_time"`    // 上次落子时间戳
	TimePerPlayer   int64           `json:"time_per_player" bson:"time_per_player"`  // 每位玩家总时间（秒）
}

// NewGame 创建一个新的游戏实例
func NewGame() *Game {
	board := NewBoard()
	initialHash := board.StateHash()
	history := make(map[string]bool)
	history[initialHash] = true

	// 中国围棋规则：每方 1 小时（3600 秒）
	const defaultTimePerPlayer = 3600

	return &Game{
		Board:         board,
		History:       history,
		NextPlayer:    Black,
		Status:        GameStatusWaiting,
		BlackTimeLeft: defaultTimePerPlayer,
		WhiteTimeLeft: defaultTimePerPlayer,
		TimePerPlayer: defaultTimePerPlayer,
	}
}

// NewGameWithPlayer 创建一个由指定玩家发起的游戏
func NewGameWithPlayer(playerID string, isAIGame bool) *Game {
	g := NewGame()
	g.PlayerBlack = playerID
	g.IsAIGame = isAIGame
	
	if isAIGame {
		g.PlayerWhite = "AI"
		g.Status = GameStatusPlaying // AI 游戏立即开始
		g.LastMoveTime = getCurrentTimestamp() // 记录游戏开始时间
	}
	
	return g
}

// CanPlayerMove 检查指定玩家是否可以在当前回合落子
func (g *Game) CanPlayerMove(playerID string) bool {
	if g.GameOver {
		return false
	}
	
	if g.Status != GameStatusPlaying {
		return false
	}
	
	// 检查是否轮到该玩家
	if g.NextPlayer == Black {
		return g.PlayerBlack == playerID
	}
	return g.PlayerWhite == playerID
}

// JoinGame 玩家加入游戏（作为白棋）
func (g *Game) JoinGame(playerID string) error {
	if g.Status != GameStatusWaiting {
		return errors.New("game is not waiting for players")
	}
	
	if g.PlayerBlack == playerID {
		return errors.New("cannot join your own game")
	}
	
	if g.PlayerWhite != "" {
		return errors.New("game is full")
	}
	
	g.PlayerWhite = playerID
	g.Status = GameStatusPlaying
	g.LastMoveTime = getCurrentTimestamp() // 记录游戏开始时间
	return nil
}

// PlayMove 是进行一步棋的核心方法，采用克隆模式保证原子性
func (g *Game) PlayMove(p Point) error {
	if g.GameOver {
		return errors.New("game is over")
	}

	// 0. 更新时间
	if err := g.UpdateTime(); err != nil {
		return err // 超时
	}

	// 1. 克隆棋盘，在副本上操作
	tempBoard := g.Board.Clone()

	// 2. 在克隆的棋盘上尝试落子
	captures, err := tempBoard.PlaceStone(g.NextPlayer, p)
	if err != nil {
		return err // 来自 PlaceStone 的错误 (越界, 非空, 自杀)
	}

	// 3. 检查 Ko 规则
	newHash := tempBoard.StateHash()
	if g.History[newHash] {
		return ErrKoViolation
	}

	// 4. 所有检查通过，正式更新游戏状态
	g.Board = tempBoard // 将主棋盘指向新的状态
	g.History[newHash] = true
	g.NextPlayer = getOpponent(g.NextPlayer)
	g.Passes = 0               // 任何成功的落子都会重置pass计数
	if g.NextPlayer == Black { // 刚刚是白棋下的
		g.CapturesByW += captures
	} else { // 刚刚是黑棋下的
		g.CapturesByB += captures
	}

	return nil
}

// PassTurn 处理玩家虚手
func (g *Game) PassTurn() error {
	if g.GameOver {
		return errors.New("game is over")
	}

	// 更新时间
	if err := g.UpdateTime(); err != nil {
		return err // 超时
	}

	g.Passes++
	g.NextPlayer = getOpponent(g.NextPlayer)

	if g.Passes >= 2 {
		g.GameOver = true
		g.Status = GameStatusFinished
	}

	return nil
}

// 后期需要修改替换或者完全优化
// CalculateScore 根据中国规则计算最终得分
// 简化：假设终局时棋盘上所有棋子都是活棋
func (g *Game) CalculateScore() (ScoreResult, error) {
	if !g.GameOver {
		return ScoreResult{}, errors.New("game is not over yet")
	}

	blackStones := 0
	whiteStones := 0
	blackTerritory := 0
	whiteTerritory := 0

	visited := [BoardSize][BoardSize]bool{}

	// 1. 计算双方棋子数
	for i := 0; i < BoardSize; i++ {
		for j := 0; j < BoardSize; j++ {
			switch g.Board.Grid[i][j] {
			case Black:
				blackStones++
			case White:
				whiteStones++
			}
		}
	}

	// 2. 使用BFS计算领地
	for i := 0; i < BoardSize; i++ {
		for j := 0; j < BoardSize; j++ {
			if g.Board.Grid[i][j] == Empty && !visited[i][j] {
				q := []Point{{i, j}}
				visited[i][j] = true
				area := 0
				touchesBlack := false
				touchesWhite := false

				for len(q) > 0 {
					current := q[0]
					q = q[1:]
					area++

					for _, n := range getNeighbors(current) {
						if g.Board.Grid[n.X][n.Y] == Black {
							touchesBlack = true
						} else if g.Board.Grid[n.X][n.Y] == White {
							touchesWhite = true
						} else if !visited[n.X][n.Y] {
							visited[n.X][n.Y] = true
							q = append(q, n)
						}
					}
				}

				if touchesBlack && !touchesWhite {
					blackTerritory += area
				} else if !touchesBlack && touchesWhite {
					whiteTerritory += area
				}
			}
		}
	}

	result := ScoreResult{
		BlackScore: float64(blackStones + blackTerritory),
		WhiteScore: float64(whiteStones+whiteTerritory) + 3.75, // Komi for White
	}

	// 根据规则，黑棋得分 > 184.25 才算赢
	if result.BlackScore > 184.25 {
		result.Winner = Black
	} else {
		result.Winner = White
	}

	return result, nil
}

// getCurrentTimestamp 获取当前时间戳（秒）
func getCurrentTimestamp() int64 {
	return time.Now().Unix()
}

// UpdateTime 更新玩家剩余时间
func (g *Game) UpdateTime() error {
	if g.GameOver || g.Status != GameStatusPlaying {
		return nil
	}
	
	if g.LastMoveTime == 0 {
		g.LastMoveTime = getCurrentTimestamp()
		return nil
	}
	
	// 计算经过的时间
	now := getCurrentTimestamp()
	elapsed := now - g.LastMoveTime
	
	// 扣除当前玩家的时间
	if g.NextPlayer == Black {
		g.BlackTimeLeft -= elapsed
		if g.BlackTimeLeft <= 0 {
			g.BlackTimeLeft = 0
			g.GameOver = true
			return ErrTimeOut
		}
	} else {
		g.WhiteTimeLeft -= elapsed
		if g.WhiteTimeLeft <= 0 {
			g.WhiteTimeLeft = 0
			g.GameOver = true
			return ErrTimeOut
		}
	}
	
	g.LastMoveTime = now
	return nil
}

// GetTimeLeft 获取当前玩家剩余时间
func (g *Game) GetTimeLeft() int64 {
	if g.NextPlayer == Black {
		return g.BlackTimeLeft
	}
	return g.WhiteTimeLeft
}
