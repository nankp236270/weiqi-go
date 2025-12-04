package ai

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/nankp236270/weiqi-go/game"
)

// Client 是 AI 服务的客户端
type Client struct {
	baseURL    string
	httpClient *http.Client
}

// NewClient 创建一个新的 AI 客户端
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// MoveRequest 是请求 AI 落子的请求体
type MoveRequest struct {
	Board      [][]int8 `json:"board"`
	NextPlayer int8     `json:"next_player"`
	History    []string `json:"history"`
}

// MoveResponse 是 AI 返回的落子响应
type MoveResponse struct {
	X          int     `json:"x"`
	Y          int     `json:"y"`
	Confidence float64 `json:"confidence"`
}

// ScoreRequest 是请求计分的请求体
type ScoreRequest struct {
	Board [][]int8 `json:"board"`
}

// ScoreResponse 是计分响应
type ScoreResponse struct {
	BlackScore float64     `json:"black_score"`
	WhiteScore float64     `json:"white_score"`
	Winner     game.Player `json:"winner"`
}

// GetMove 从 AI 服务获取下一步落子
func (c *Client) GetMove(g *game.Game) (game.Point, error) {
	// 构建历史记录列表
	history := make([]string, 0, len(g.History))
	for hash := range g.History {
		history = append(history, hash)
	}

	// 转换棋盘为数字数组
	board := make([][]int8, game.BoardSize)
	for i := 0; i < game.BoardSize; i++ {
		board[i] = make([]int8, game.BoardSize)
		for j := 0; j < game.BoardSize; j++ {
			board[i][j] = int8(g.Board.Grid[i][j])
		}
	}

	// 构建请求
	reqBody := MoveRequest{
		Board:      board,
		NextPlayer: int8(g.NextPlayer),
		History:    history,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return game.Point{}, fmt.Errorf("failed to marshal request: %w", err)
	}

	// 发送请求
	url := fmt.Sprintf("%s/v1/ai/move", c.baseURL)
	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return game.Point{}, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return game.Point{}, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return game.Point{}, fmt.Errorf("AI service returned error: %s (status %d)", string(body), resp.StatusCode)
	}

	// 解析响应
	var moveResp MoveResponse
	if err := json.Unmarshal(body, &moveResp); err != nil {
		return game.Point{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return game.Point{X: moveResp.X, Y: moveResp.Y}, nil
}

// CalculateScore 从 AI 服务获取终局计分
func (c *Client) CalculateScore(g *game.Game) (game.ScoreResult, error) {
	// 转换棋盘为数字数组
	board := make([][]int8, game.BoardSize)
	for i := 0; i < game.BoardSize; i++ {
		board[i] = make([]int8, game.BoardSize)
		for j := 0; j < game.BoardSize; j++ {
			board[i][j] = int8(g.Board.Grid[i][j])
		}
	}

	// 构建请求
	reqBody := ScoreRequest{
		Board: board,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return game.ScoreResult{}, fmt.Errorf("failed to marshal request: %w", err)
	}

	// 发送请求
	url := fmt.Sprintf("%s/v1/game/score", c.baseURL)
	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return game.ScoreResult{}, fmt.Errorf("failed to call AI service: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return game.ScoreResult{}, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return game.ScoreResult{}, fmt.Errorf("AI service returned error: %s (status %d)", string(body), resp.StatusCode)
	}

	// 解析响应
	var scoreResp ScoreResponse
	if err := json.Unmarshal(body, &scoreResp); err != nil {
		return game.ScoreResult{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return game.ScoreResult{
		BlackScore: scoreResp.BlackScore,
		WhiteScore: scoreResp.WhiteScore,
		Winner:     scoreResp.Winner,
	}, nil
}

// HealthCheck 检查 AI 服务是否健康
func (c *Client) HealthCheck() error {
	url := fmt.Sprintf("%s/health", c.baseURL)
	resp, err := c.httpClient.Get(url)
	if err != nil {
		return fmt.Errorf("failed to connect to AI service: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("AI service unhealthy: status %d", resp.StatusCode)
	}

	return nil
}

