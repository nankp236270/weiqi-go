package game

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
)

// BoardSize 定义了棋盘的大小
const BoardSize = 19

// Player 定义了棋盘上的点的状态: 空, 黑棋, 白棋
type Player int8

const (
	Empty Player = 0
	Black Player = 1
	White Player = 2
)

// MarshalJSON 自定义 JSON 序列化
func (p Player) MarshalJSON() ([]byte, error) {
	switch p {
	case Black:
		return []byte(`"Black"`), nil
	case White:
		return []byte(`"White"`), nil
	default:
		return []byte(`"Empty"`), nil
	}
}

// UnmarshalJSON 自定义 JSON 反序列化
func (p *Player) UnmarshalJSON(data []byte) error {
	str := string(data)
	switch str {
	case `"Black"`, `"black"`, `"1"`:
		*p = Black
	case `"White"`, `"white"`, `"2"`:
		*p = White
	default:
		*p = Empty
	}
	return nil
}

// Point 定义了棋盘上的一个坐标
type Point struct {
	X int `json:"x"`
	Y int `json:"y"`
}

// Board 定义了棋盘的结构
type Board struct {
	Grid [BoardSize][BoardSize]Player `json:"-"`
}

// MarshalJSON 自定义 Board 的 JSON 序列化，将 Grid 转换为数字数组
func (b *Board) MarshalJSON() ([]byte, error) {
	// 创建数字数组
	grid := make([][]int8, BoardSize)
	for i := 0; i < BoardSize; i++ {
		grid[i] = make([]int8, BoardSize)
		for j := 0; j < BoardSize; j++ {
			grid[i][j] = int8(b.Grid[i][j])
		}
	}
	
	// 序列化为 JSON
	type Alias struct {
		Grid [][]int8 `json:"grid"`
	}
	return json.Marshal(&Alias{
		Grid: grid,
	})
}

// UnmarshalJSON 自定义 Board 的 JSON 反序列化
func (b *Board) UnmarshalJSON(data []byte) error {
	type Alias struct {
		Grid [][]int8 `json:"grid"`
	}
	var alias Alias
	if err := json.Unmarshal(data, &alias); err != nil {
		return err
	}
	
	// 转换回 Player 类型
	for i := 0; i < BoardSize && i < len(alias.Grid); i++ {
		for j := 0; j < BoardSize && j < len(alias.Grid[i]); j++ {
			b.Grid[i][j] = Player(alias.Grid[i][j])
		}
	}
	
	return nil
}

// 定义一些常亮错误, 便于调用方法判断
var (
	ErrPointOutOfBounds = errors.New("point is outside the board")
	ErrPointNotEmpty    = errors.New("point is not empty")
	ErrSuicideMove      = errors.New("suicide move is not allowed")
)

// NewBoard 创建并返回一个空的棋盘
func NewBoard() *Board {
	return &Board{}
}

// PlaceStone 在指定坐标落下指定颜色的旗子
// 包含了对落子合法性的基础检查
// 它会处理提子逻辑，并返回提子的数量
func (b *Board) PlaceStone(player Player, p Point) (captures int, err error) {
	// 1. 基础合法性检查
	// 检查坐标是否在棋盘内
	if p.X < 0 || p.X >= BoardSize || p.Y < 0 || p.Y >= BoardSize {
		return 0, ErrPointOutOfBounds
	}
	// 检查该位置是否为空
	// 注意：Grid[行][列]，而 Point.X 是列，Point.Y 是行
	if b.Grid[p.Y][p.X] != Empty {
		return 0, ErrPointNotEmpty
	}

	// 2. 试探性地落子
	b.Grid[p.Y][p.X] = player

	// 3. 检查并移除对方被提的子
	opponent := getOpponent(player)
	var capturedStones []Point
	for _, n := range getNeighbors(p) {
		if b.Grid[n.Y][n.X] == opponent {
			group, liberties := b.findGroupAndLiberties(n)
			if liberties == 0 {
				capturedStones = append(capturedStones, group...)
				for _, stone := range group {
					b.Grid[stone.Y][stone.X] = Empty
				}
			}
		}
	}

	// 4. 自杀禁令检查
	// 在提子后，检查落子点所在的棋块是否还有气
	_, newLiberties := b.findGroupAndLiberties(p)
	if newLiberties == 0 {
		// 这是一个自杀点，回滚所有操作
		b.Grid[p.Y][p.X] = Empty               // 撤销落子
		for _, stone := range capturedStones { // 将被提的子放回去
			b.Grid[stone.Y][stone.X] = opponent
		}
		return 0, ErrSuicideMove
	}

	return len(capturedStones), nil
}

// findGroupAndLiberties 使用广度优先搜索(BFS)寻找一个点所在的棋块及其气数
// visitedInGroup 用于记录棋块内的点，防止重复搜索
// visitedLiberties 用于记录气点，防止重复计数
func (b *Board) findGroupAndLiberties(startPoint Point) (group []Point, liberties int) {
	if b.Grid[startPoint.Y][startPoint.X] == Empty {
		return nil, 0
	}

	player := b.Grid[startPoint.Y][startPoint.X]
	q := []Point{startPoint}
	visitedInGroup := map[Point]bool{startPoint: true}
	visitedLiberties := map[Point]bool{}

	for len(q) > 0 {
		current := q[0]
		q = q[1:]
		group = append(group, current)

		for _, n := range getNeighbors(current) {
			switch b.Grid[n.Y][n.X] {
			case Empty:
				if !visitedLiberties[n] {
					visitedLiberties[n] = true
				}
			case player:
				if !visitedInGroup[n] {
					visitedInGroup[n] = true
					q = append(q, n)
				}
			}
		}
	}

	return group, len(visitedLiberties)
}

// getNeighbors 返回一个点的所有合法邻居坐标
func getNeighbors(p Point) []Point {
	neighbors := make([]Point, 0, 4)
	if p.X > 0 {
		neighbors = append(neighbors, Point{X: p.X - 1, Y: p.Y})
	}
	if p.X < BoardSize-1 {
		neighbors = append(neighbors, Point{X: p.X + 1, Y: p.Y})
	}
	if p.Y > 0 {
		neighbors = append(neighbors, Point{X: p.X, Y: p.Y - 1})
	}
	if p.Y < BoardSize-1 {
		neighbors = append(neighbors, Point{X: p.X, Y: p.Y + 1})
	}
	return neighbors
}

// getOpponent 返回对手的颜色
func getOpponent(player Player) Player {
	if player == Black {
		return White
	}
	return Black
}

// StateHash 将当前棋盘状态转换为一个唯一的字符串，用作哈希键
func (b *Board) StateHash() string {
	var sb strings.Builder
	sb.Grow(BoardSize * BoardSize) // 预分配内存以提高性能
	for i := 0; i < BoardSize; i++ {
		for j := 0; j < BoardSize; j++ {
			sb.WriteByte(byte(b.Grid[i][j]) + '0') // 将 0,1,2 转换为 '0','1','2'
		}
	}
	return sb.String()
}

// Clone 创建并返回当前棋盘的一个深拷贝
func (b *Board) Clone() *Board {
	clone := NewBoard()
	clone.Grid = b.Grid // 在 Go 中，数组是值类型，直接赋值就是拷贝
	return clone
}

// String 方法让 Board 类型可以被方便地被打印出来, 用于调试
func (b *Board) String() string {
	var sb strings.Builder
	sb.WriteString("   ")
	for i := 0; i < BoardSize; i++ {
		sb.WriteString(fmt.Sprintf("%2d ", i))
	}
	sb.WriteString("\n")

	for i := 0; i < BoardSize; i++ {
		sb.WriteString(fmt.Sprintf("%2d ", i))
		for j := 0; j < BoardSize; j++ {
			switch b.Grid[i][j] {
			case Empty:
				sb.WriteString(" . ")
			case Black:
				sb.WriteString(" X ")
			case White:
				sb.WriteString(" O ")
			}
		}
		sb.WriteString("\n")
	}
	return sb.String()
}
