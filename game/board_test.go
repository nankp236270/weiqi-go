package game

import (
	"errors"
	"testing"
)

// TestNewBoard 验证新创建的棋盘是否为空
func TestNewBoard(t *testing.T) {
	board := NewBoard()
	for i := 0; i < BoardSize; i++ {
		for j := 0; j < BoardSize; j++ {
			if board.Grid[i][j] != Empty {
				t.Fatalf("Expected board to be empty, but found a stone at (%d, %d)", i, j)
			}
		}
	}
}

// TestPlaceStone_ValidMove 测试合法的落子
func TestPlaceStone_ValidMove(t *testing.T) {
	board := NewBoard()
	p := Point{X: 5, Y: 5}
	player := Black

	_, err := board.PlaceStone(player, p)

	if err != nil {
		t.Fatalf("Expected no error, but got %v", err)
	}
	if board.Grid[p.X][p.Y] != player {
		t.Fatalf("Expected stone at (%d, %d) to be %v, but it was not", p.X, p.Y, player)
	}
}

// TestPlaceStone_NotEmpty 测试在已有棋子的位置落子
func TestPlaceStone_NotEmpty(t *testing.T) {
	board := NewBoard()
	p := Point{X: 10, Y: 10}

	// 先下一个子
	_, _ = board.PlaceStone(Black, p)

	// 尝试在同一个位置再下一个子
	_, err := board.PlaceStone(White, p)

	if !errors.Is(err, ErrPointNotEmpty) {
		t.Fatalf("Expected ErrPointNotEmpty, but got %v", err)
	}
}

// TestCaptureSingleStone 测试提掉单个子的情况
func TestCaptureSingleStone(t *testing.T) {
	board := NewBoard()
	// 设置一个被包围的白子
	// . X .
	// X O X
	// . X .
	board.Grid[0][1] = Black
	board.Grid[1][0] = Black
	board.Grid[1][2] = Black
	board.Grid[1][1] = White // 被包围的白子

	// 黑棋在 (2,1) 落子，完成包围并提子
	captures, err := board.PlaceStone(Black, Point{X: 2, Y: 1})
	if err != nil {
		t.Fatalf("Expected no error, but got %v", err)
	}

	if captures != 1 {
		t.Fatalf("Expected 1 capture, but got %d", captures)
	}

	if board.Grid[1][1] != Empty {
		t.Fatalf("Expected stone at (1,1) to be captured and removed")
	}
}

// TestCaptureMultipleStones 测试提掉一个棋块的情况
func TestCaptureMultipleStones_01(t *testing.T) {
	board := NewBoard()
	// 设置一个被包围的白棋块
	// X X X .
	// X O O X
	// X X X .
	board.Grid[0][0] = Black
	board.Grid[0][1] = Black
	board.Grid[0][2] = Black
	board.Grid[1][0] = Black
	board.Grid[1][2] = Black
	board.Grid[2][0] = Black
	board.Grid[2][2] = Black

	board.Grid[1][1] = White // 白棋块
	board.Grid[2][1] = White // 白棋块

	// 白棋块唯一的“气”在 (3,1)
	// 黑棋在 (3,1) 落子，提掉白棋块
	captures, err := board.PlaceStone(Black, Point{X: 3, Y: 1})
	if err != nil {
		t.Fatalf("Expected no error, but got %v", err)
	}

	if captures != 2 {
		t.Fatalf("Expected 2 captures, but got %d", captures)
	}

	if board.Grid[1][1] != Empty || board.Grid[2][1] != Empty {
		t.Fatalf("Expected white group to be captured")
	}
}

// TestCaptureMultipleStones 测试提掉一个棋块的情况
func TestCaptureMultipleStones_02(t *testing.T) {
	board := NewBoard()
	// 设置一个被包围的白棋块 { (0,1), (0,2) }
	// 这个棋块唯一的“气”在 (0,0)
	// . O O X
	// X X X X
	board.Grid[0][1] = White // 白棋块
	board.Grid[0][2] = White // 白棋块

	board.Grid[0][3] = Black
	board.Grid[1][0] = Black
	board.Grid[1][1] = Black
	board.Grid[1][2] = Black
	board.Grid[1][3] = Black

	// 黑棋在 (0,0) 落子，提掉白棋块
	// 这一子落下后，会与 (0,1) 的白子相邻，触发检查
	captures, err := board.PlaceStone(Black, Point{X: 0, Y: 0})
	if err != nil {
		t.Fatalf("Expected no error, but got %v", err)
	}

	if captures != 2 {
		t.Fatalf("Expected 2 captures, but got %d", captures)
	}

	if board.Grid[0][1] != Empty || board.Grid[0][2] != Empty {
		t.Fatalf("Expected white group to be captured")
	}
}

// TestSuicide_Simple 测试一个简单的非法自杀落子
func TestSuicide_Simple(t *testing.T) {
	board := NewBoard()
	// . X .
	// X . X
	// . X .
	board.Grid[0][1] = Black
	board.Grid[1][0] = Black
	board.Grid[1][2] = Black
	board.Grid[2][1] = Black

	// 白棋试图在(1,1)这个禁入点落子
	_, err := board.PlaceStone(White, Point{X: 1, Y: 1})
	if !errors.Is(err, ErrSuicideMove) {
		t.Fatalf("Expected ErrSuicideMove, but got %v", err)
	}

	// 确认棋盘在非法落子后没有被改变
	if board.Grid[1][1] != Empty {
		t.Fatalf("Board should not be modified after an illegal move")
	}
}

// TestSuicide_WithCaptureAllowed 测试一个看似自杀但因提子而合法的落子 (吃子活棋)
func TestSuicide_WithCaptureAllowed(t *testing.T) {
	board := NewBoard()
	// . B W .
	// B W . W
	// . B W .
	board.Grid[0][1] = Black
	board.Grid[1][0] = Black
	board.Grid[1][2] = Black

	board.Grid[2][0] = White
	board.Grid[1][1] = White // 这个白棋块处于"打吃"状态
	board.Grid[2][2] = White

	// 黑棋在(2,1)落子。这个位置会填满黑棋块自己的最后一气,
	// 但因为它同时提掉了白棋块, 从而获得了新的气, 所以是合法的。
	captures, err := board.PlaceStone(Black, Point{X: 2, Y: 1})
	if err != nil {
		t.Fatalf("Expected a valid move, but got error %v", err)
	}
	if captures != 1 {
		t.Fatalf("Expected 1 captures, but got %d", captures)
	}
	if board.Grid[2][1] != Black {
		t.Fatalf("The move at (2,1) should be successful")
	}
	if board.Grid[1][1] != Empty {
		t.Fatalf("Black group should have been captured")
	}
}
