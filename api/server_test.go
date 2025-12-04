package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/nankp236270/weiqi-go/game"
	"github.com/nankp236270/weiqi-go/storage"
)

// TestCreateGame 测试创建游戏的 API
func TestCreateGame(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	req, _ := http.NewRequest("POST", "/v1/games", nil)
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("Expected status %d, got %d", http.StatusCreated, w.Code)
	}

	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	// 验证响应包含 game_id
	gameID, ok := response["game_id"].(string)
	if !ok || gameID == "" {
		t.Fatal("Expected game_id in response")
	}

	// 验证响应包含初始状态
	state, ok := response["state"].(map[string]interface{})
	if !ok {
		t.Fatal("Expected state in response")
	}

	// 验证初始状态
	nextPlayer := state["next_player"].(float64)
	if int(nextPlayer) != int(game.Black) {
		t.Fatalf("Expected next_player to be Black (1), got %v", nextPlayer)
	}

	gameOver := state["game_over"].(bool)
	if gameOver {
		t.Fatal("Expected game_over to be false")
	}
}

// TestGetGame 测试获取游戏状态的 API
func TestGetGame(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 先创建一个游戏
	gameID := "test-game-123"
	g := game.NewGame()
	_ = store.CreateGame(gameID, g)

	// 获取游戏状态
	req, _ := http.NewRequest("GET", "/v1/games/"+gameID, nil)
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d", http.StatusOK, w.Code)
	}

	var response game.Game
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	if response.NextPlayer != game.Black {
		t.Fatal("Expected next_player to be Black")
	}
}

// TestGetGame_NotFound 测试获取不存在的游戏
func TestGetGame_NotFound(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	req, _ := http.NewRequest("GET", "/v1/games/nonexistent", nil)
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("Expected status %d, got %d", http.StatusNotFound, w.Code)
	}
}

// TestPlayMove 测试落子 API
func TestPlayMove(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 创建游戏
	gameID := "test-game-456"
	g := game.NewGame()
	_ = store.CreateGame(gameID, g)

	// 落子
	moveData := map[string]int{"x": 3, "y": 3}
	jsonData, _ := json.Marshal(moveData)

	req, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/move", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d. Body: %s", http.StatusOK, w.Code, w.Body.String())
	}

	var response game.Game
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	// 验证落子成功
	if response.Board.Grid[3][3] != game.Black {
		t.Fatal("Expected black stone at (3,3)")
	}

	// 验证轮次切换
	if response.NextPlayer != game.White {
		t.Fatal("Expected next_player to be White")
	}
}

// TestPlayMove_InvalidMove 测试非法落子
func TestPlayMove_InvalidMove(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 创建游戏并落一子
	gameID := "test-game-789"
	g := game.NewGame()
	_ = g.PlayMove(game.Point{X: 3, Y: 3})
	_ = store.CreateGame(gameID, g)

	// 尝试在同一位置落子
	moveData := map[string]int{"x": 3, "y": 3}
	jsonData, _ := json.Marshal(moveData)

	req, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/move", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("Expected status %d, got %d", http.StatusBadRequest, w.Code)
	}
}

// TestPlayMove_InvalidJSON 测试无效的 JSON 请求
func TestPlayMove_InvalidJSON(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	gameID := "test-game-abc"
	g := game.NewGame()
	_ = store.CreateGame(gameID, g)

	// 发送无效的 JSON
	req, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/move", bytes.NewBufferString("{invalid json}"))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("Expected status %d, got %d", http.StatusBadRequest, w.Code)
	}
}

// TestPassTurn 测试虚手 API
func TestPassTurn(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 创建游戏
	gameID := "test-game-pass"
	g := game.NewGame()
	_ = store.CreateGame(gameID, g)

	// 第一次虚手
	req, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/pass", nil)
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d", http.StatusOK, w.Code)
	}

	var response game.Game
	err := json.Unmarshal(w.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	if response.Passes != 1 {
		t.Fatalf("Expected 1 pass, got %d", response.Passes)
	}
	if response.GameOver {
		t.Fatal("Game should not be over after one pass")
	}
}

// TestPassTurn_GameOver 测试连续虚手导致游戏结束
func TestPassTurn_GameOver(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 创建游戏
	gameID := "test-game-pass-over"
	g := game.NewGame()
	_ = store.CreateGame(gameID, g)

	// 第一次虚手
	req1, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/pass", nil)
	w1 := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w1, req1)

	// 第二次虚手
	req2, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/pass", nil)
	w2 := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w2, req2)

	if w2.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d", http.StatusOK, w2.Code)
	}

	var response map[string]interface{}
	err := json.Unmarshal(w2.Body.Bytes(), &response)
	if err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	// 验证游戏结束
	message, ok := response["message"].(string)
	if !ok || message != "game over" {
		t.Fatal("Expected 'game over' message")
	}

	// 验证包含计分结果
	_, hasScore := response["score"]
	if !hasScore {
		t.Fatal("Expected score in response")
	}
}

// TestCompleteGameFlow 测试完整的游戏流程
func TestCompleteGameFlow(t *testing.T) {
	store := storage.NewInMemoryGameStore()
	server := NewServer(":8080", store)

	// 1. 创建游戏
	req, _ := http.NewRequest("POST", "/v1/games", nil)
	w := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w, req)

	var createResponse map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &createResponse)
	gameID := createResponse["game_id"].(string)

	// 2. 黑棋落子
	move1 := map[string]int{"x": 3, "y": 3}
	jsonData1, _ := json.Marshal(move1)
	req1, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/move", bytes.NewBuffer(jsonData1))
	req1.Header.Set("Content-Type", "application/json")
	w1 := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w1, req1)

	if w1.Code != http.StatusOK {
		t.Fatalf("Black move failed: %s", w1.Body.String())
	}

	// 3. 白棋落子
	move2 := map[string]int{"x": 3, "y": 4}
	jsonData2, _ := json.Marshal(move2)
	req2, _ := http.NewRequest("POST", "/v1/games/"+gameID+"/move", bytes.NewBuffer(jsonData2))
	req2.Header.Set("Content-Type", "application/json")
	w2 := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w2, req2)

	if w2.Code != http.StatusOK {
		t.Fatalf("White move failed: %s", w2.Body.String())
	}

	// 4. 获取游戏状态
	req3, _ := http.NewRequest("GET", "/v1/games/"+gameID, nil)
	w3 := httptest.NewRecorder()
	server.httpServer.Handler.ServeHTTP(w3, req3)

	var finalState game.Game
	json.Unmarshal(w3.Body.Bytes(), &finalState)

	// 验证棋盘状态
	if finalState.Board.Grid[3][3] != game.Black {
		t.Fatal("Expected black stone at (3,3)")
	}
	if finalState.Board.Grid[3][4] != game.White {
		t.Fatal("Expected white stone at (3,4)")
	}
	if finalState.NextPlayer != game.Black {
		t.Fatal("Expected next player to be Black")
	}
}

