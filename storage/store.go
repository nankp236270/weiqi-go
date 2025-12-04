package storage

import (
	"fmt"
	"sync"

	"github.com/nankp236270/weiqi-go/game"
)

// GameStore 定义了游戏数据持久化层所需要实现的方法
type GameStore interface {
	CreateGame(gameID string, g *game.Game) error
	GetGame(gameID string) (*game.Game, error)
	UpdateGame(gameID string, g *game.Game) error
	GetGamesByPlayer(playerID string) ([]GameInfo, error)
	GetWaitingGames() ([]GameInfo, error)
}

// GameInfo 游戏信息（用于列表）
type GameInfo struct {
	ID          string          `json:"id"`
	PlayerBlack string          `json:"player_black"`
	PlayerWhite string          `json:"player_white"`
	Status      game.GameStatus `json:"status"`
	IsAIGame    bool            `json:"is_ai_game"`
	NextPlayer  game.Player     `json:"next_player"`
	GameOver    bool            `json:"game_over"`
}

// InMemoryGameStore 是 GameStore 接口的一个内存实现
type InMemoryGameStore struct {
	store map[string]*game.Game
	mu    sync.RWMutex
}

// NewInMemoryGameStore 创建一个新的内存存储实例
func NewInMemoryGameStore() *InMemoryGameStore {
	return &InMemoryGameStore{
		store: make(map[string]*game.Game),
	}
}

func (s *InMemoryGameStore) CreateGame(gameID string, g *game.Game) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.store[gameID] = g
	return nil
}

func (s *InMemoryGameStore) GetGame(gameID string) (*game.Game, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	g, ok := s.store[gameID]
	if !ok {
		return nil, fmt.Errorf("game with ID %s not found", gameID)
	}
	return g, nil
}

func (s *InMemoryGameStore) UpdateGame(gameID string, g *game.Game) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.store[gameID]; !ok {
		return fmt.Errorf("game with ID %s not found", gameID)
	}

	s.store[gameID] = g
	return nil
}

func (s *InMemoryGameStore) GetGamesByPlayer(playerID string) ([]GameInfo, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var games []GameInfo
	for id, g := range s.store {
		if g.PlayerBlack == playerID || g.PlayerWhite == playerID {
			games = append(games, GameInfo{
				ID:          id,
				PlayerBlack: g.PlayerBlack,
				PlayerWhite: g.PlayerWhite,
				Status:      g.Status,
				IsAIGame:    g.IsAIGame,
				NextPlayer:  g.NextPlayer,
				GameOver:    g.GameOver,
			})
		}
	}
	return games, nil
}

func (s *InMemoryGameStore) GetWaitingGames() ([]GameInfo, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var games []GameInfo
	for id, g := range s.store {
		if g.Status == game.GameStatusWaiting {
			games = append(games, GameInfo{
				ID:          id,
				PlayerBlack: g.PlayerBlack,
				PlayerWhite: g.PlayerWhite,
				Status:      g.Status,
				IsAIGame:    g.IsAIGame,
				NextPlayer:  g.NextPlayer,
				GameOver:    g.GameOver,
			})
		}
	}
	return games, nil
}
