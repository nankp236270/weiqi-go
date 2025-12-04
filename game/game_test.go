package game

import (
	"errors"
	"testing"
)

// TestNewGame 验证新游戏的初始状态
func TestNewGame(t *testing.T) {
	g := NewGame()

	if g.NextPlayer != Black {
		t.Fatalf("Expected first player to be Black, got %v", g.NextPlayer)
	}
	if g.GameOver {
		t.Fatal("Expected new game not to be over")
	}
	if g.Passes != 0 {
		t.Fatalf("Expected 0 passes, got %d", g.Passes)
	}
	if len(g.History) != 1 {
		t.Fatalf("Expected history to contain initial state, got %d entries", len(g.History))
	}
}

// TestPlayMove_ValidMove 测试合法的落子
func TestPlayMove_ValidMove(t *testing.T) {
	g := NewGame()
	p := Point{X: 3, Y: 3}

	err := g.PlayMove(p)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if g.Board.Grid[p.X][p.Y] != Black {
		t.Fatal("Expected black stone at (3,3)")
	}
	if g.NextPlayer != White {
		t.Fatal("Expected next player to be White")
	}
	if g.Passes != 0 {
		t.Fatal("Expected passes to be reset to 0")
	}
}

// TestPlayMove_InvalidMove 测试非法落子
func TestPlayMove_InvalidMove(t *testing.T) {
	g := NewGame()
	p := Point{X: 3, Y: 3}

	// 第一次落子应该成功
	_ = g.PlayMove(p)

	// 尝试在同一位置再次落子
	err := g.PlayMove(p)
	if !errors.Is(err, ErrPointNotEmpty) {
		t.Fatalf("Expected ErrPointNotEmpty, got %v", err)
	}

	// 确认轮次没有改变
	if g.NextPlayer != White {
		t.Fatal("Expected next player to still be White after invalid move")
	}
}

// TestKoRule_SimpleKo 测试简单的劫争（Ko）规则
func TestKoRule_SimpleKo(t *testing.T) {
	g := NewGame()

	// 设置一个典型的劫争局面
	// . X O .
	// X O . O
	// . X O .
	// . . . .
	g.Board.Grid[0][1] = Black
	g.Board.Grid[1][0] = Black
	g.Board.Grid[2][1] = Black

	g.Board.Grid[0][2] = White
	g.Board.Grid[1][1] = White
	g.Board.Grid[1][3] = White
	g.Board.Grid[2][2] = White

	// 更新历史记录
	g.History[g.Board.StateHash()] = true

	// 黑棋在 (1,2) 落子，提掉白棋 (1,1)
	g.NextPlayer = Black
	err := g.PlayMove(Point{X: 1, Y: 2})
	if err != nil {
		t.Fatalf("Expected valid move, got error: %v", err)
	}

	// 验证白子被提掉
	if g.Board.Grid[1][1] != Empty {
		t.Fatal("Expected white stone at (1,1) to be captured")
	}
	if g.CapturesByB != 1 {
		t.Fatalf("Expected 1 capture by Black, got %d", g.CapturesByB)
	}

	// 现在轮到白棋，白棋尝试立即在 (1,1) 提回来
	// 这应该违反 Ko 规则
	err = g.PlayMove(Point{X: 1, Y: 1})
	if !errors.Is(err, ErrKoViolation) {
		t.Fatalf("Expected ErrKoViolation, got %v", err)
	}

	// 验证棋盘状态没有改变
	if g.Board.Grid[1][1] != Empty {
		t.Fatal("Board should not change after Ko violation")
	}
	if g.NextPlayer != White {
		t.Fatal("Next player should still be White after Ko violation")
	}
}

// TestKoRule_AllowedAfterOtherMove 测试在其他地方落子后可以重新提劫
func TestKoRule_AllowedAfterOtherMove(t *testing.T) {
	g := NewGame()

	// 设置劫争局面
	g.Board.Grid[0][1] = Black
	g.Board.Grid[1][0] = Black
	g.Board.Grid[2][1] = Black

	g.Board.Grid[0][2] = White
	g.Board.Grid[1][1] = White
	g.Board.Grid[1][3] = White
	g.Board.Grid[2][2] = White

	g.History[g.Board.StateHash()] = true

	// 黑棋提劫
	g.NextPlayer = Black
	_ = g.PlayMove(Point{X: 1, Y: 2})

	// 白棋在其他地方落子（不是立即提回）
	_ = g.PlayMove(Point{X: 10, Y: 10})

	// 黑棋在其他地方落子
	_ = g.PlayMove(Point{X: 10, Y: 11})

	// 现在白棋可以提回劫了（因为棋盘状态已经不同）
	err := g.PlayMove(Point{X: 1, Y: 1})
	if err != nil {
		t.Fatalf("Expected valid move after other moves, got error: %v", err)
	}

	if g.Board.Grid[1][1] != White {
		t.Fatal("Expected white stone at (1,1)")
	}
}

// TestPassTurn 测试虚手功能
func TestPassTurn(t *testing.T) {
	g := NewGame()

	// 第一次虚手
	err := g.PassTurn()
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if g.Passes != 1 {
		t.Fatalf("Expected 1 pass, got %d", g.Passes)
	}
	if g.NextPlayer != White {
		t.Fatal("Expected next player to be White")
	}
	if g.GameOver {
		t.Fatal("Game should not be over after one pass")
	}

	// 第二次虚手（连续虚手）
	err = g.PassTurn()
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if g.Passes != 2 {
		t.Fatalf("Expected 2 passes, got %d", g.Passes)
	}
	if !g.GameOver {
		t.Fatal("Game should be over after two consecutive passes")
	}
}

// TestPassTurn_ResetAfterMove 测试落子后虚手计数重置
func TestPassTurn_ResetAfterMove(t *testing.T) {
	g := NewGame()

	// 虚手一次
	_ = g.PassTurn()
	if g.Passes != 1 {
		t.Fatal("Expected 1 pass")
	}

	// 落子
	_ = g.PlayMove(Point{X: 3, Y: 3})

	// 虚手计数应该被重置
	if g.Passes != 0 {
		t.Fatalf("Expected passes to be reset to 0, got %d", g.Passes)
	}
}

// TestCaptureTracking 测试提子计数
func TestCaptureTracking(t *testing.T) {
	g := NewGame()

	// 设置一个简单的提子场景
	// . B .
	// B W B
	// . ? .
	// 白子在 (1,1) 被包围，只剩下 (2,1) 一口气
	g.Board.Grid[0][1] = Black
	g.Board.Grid[1][0] = Black
	g.Board.Grid[1][2] = Black
	g.Board.Grid[1][1] = White // 被包围的白子

	g.NextPlayer = Black
	g.History[g.Board.StateHash()] = true

	// 黑棋在 (2,1) 落子提掉白子
	err := g.PlayMove(Point{X: 2, Y: 1})
	if err != nil {
		t.Fatalf("Expected valid move, got error: %v", err)
	}

	// 验证白子被提掉
	if g.Board.Grid[1][1] != Empty {
		t.Fatal("Expected white stone at (1,1) to be captured")
	}

	// 验证提子计数
	if g.CapturesByB != 1 {
		t.Fatalf("Expected 1 capture by Black, got %d", g.CapturesByB)
	}
	if g.CapturesByW != 0 {
		t.Fatalf("Expected 0 captures by White, got %d", g.CapturesByW)
	}
}

// TestCalculateScore_GameNotOver 测试游戏未结束时不能计分
func TestCalculateScore_GameNotOver(t *testing.T) {
	g := NewGame()

	_, err := g.CalculateScore()
	if err == nil {
		t.Fatal("Expected error when calculating score for unfinished game")
	}
}

// TestCalculateScore_EmptyBoard 测试空棋盘的计分
func TestCalculateScore_EmptyBoard(t *testing.T) {
	g := NewGame()
	g.GameOver = true

	result, err := g.CalculateScore()
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// 空棋盘：黑0子，白0子 + 3.75贴子
	// 白方得分 = 0 + 3.75 = 3.75
	// 黑方需要 > 184.25 才能赢，所以白方应该赢
	if result.Winner != White {
		t.Fatalf("Expected White to win on empty board, got %v", result.Winner)
	}
}

// TestCalculateScore_SimpleGame 测试简单对局的计分
func TestCalculateScore_SimpleGame(t *testing.T) {
	g := NewGame()

	// 创建一个简单的局面：黑棋占据左上角
	// X X . . .
	// X . . . .
	// . . . . .
	g.Board.Grid[0][0] = Black
	g.Board.Grid[0][1] = Black
	g.Board.Grid[1][0] = Black

	g.GameOver = true

	result, err := g.CalculateScore()
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// 黑方应该有3个子 + 一些领地
	if result.BlackScore < 3 {
		t.Fatalf("Expected BlackScore >= 3, got %f", result.BlackScore)
	}

	// 白方有贴子 3.75
	if result.WhiteScore < 3.75 {
		t.Fatalf("Expected WhiteScore >= 3.75, got %f", result.WhiteScore)
	}
}
