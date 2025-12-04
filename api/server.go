package api

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/nankp236270/weiqi-go/auth"
	"github.com/nankp236270/weiqi-go/game"
	"github.com/nankp236270/weiqi-go/logger"
	"github.com/nankp236270/weiqi-go/storage"
	"github.com/nankp236270/weiqi-go/user"
)

// Server 负责处理 HTTP 请求
type Server struct {
	httpServer *http.Server
	store      storage.GameStore
	userStore  user.Store       // 用户存储
	aiClient   AIClient         // AI 服务客户端（可选）
	jwtManager *auth.JWTManager // JWT 管理器
}

// AIClient 定义 AI 客户端接口
type AIClient interface {
	GetMove(g *game.Game) (game.Point, error)
	CalculateScore(g *game.Game) (game.ScoreResult, error)
}

// corsMiddleware 处理 CORS 跨域请求
func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}

// NewServer 创建并配置一个新的服务器实例
func NewServer(addr string, store storage.GameStore) *Server {
	return NewServerWithAuth(addr, store, nil, nil, nil)
}

// NewServerWithAI 创建包含 AI 客户端的服务器实例
func NewServerWithAI(addr string, store storage.GameStore, aiClient AIClient) *Server {
	return NewServerWithAuth(addr, store, nil, aiClient, nil)
}

// NewServerWithAuth 创建包含完整功能的服务器实例
func NewServerWithAuth(addr string, store storage.GameStore, userStore user.Store, aiClient AIClient, jwtManager *auth.JWTManager) *Server {
	// 使用自定义的 Gin 实例（不使用默认中间件）
	router := gin.New()
	
	// 添加恢复中间件
	router.Use(gin.Recovery())
	
	// 添加 CORS 中间件
	router.Use(corsMiddleware())
	
	// 添加结构化日志中间件
	router.Use(logger.RequestLoggerMiddleware())

	server := &Server{
		store:      store,
		userStore:  userStore,
		aiClient:   aiClient,
		jwtManager: jwtManager,
	}

	// 注册路由
	v1 := router.Group("/v1")
	{
		// 认证路由（无需认证）
		if userStore != nil && jwtManager != nil {
			authGroup := v1.Group("/auth")
			{
				authGroup.POST("/register", server.register)
				authGroup.POST("/login", server.login)
				authGroup.GET("/me", auth.AuthMiddleware(jwtManager), server.me)
			}
		}

		// 游戏路由
		games := v1.Group("/games")
		{
			// 公开端点
			games.GET("/waiting", server.listWaitingGames) // 获取等待中的游戏
			games.GET("/:id", server.getGame)

			// 需要认证的端点（可选）
			if userStore != nil && jwtManager != nil {
				games.POST("", auth.AuthMiddleware(jwtManager), server.createGame)
				games.POST("/:id/join", auth.AuthMiddleware(jwtManager), server.joinGame)
				games.GET("/my", auth.AuthMiddleware(jwtManager), server.listMyGames)
			} else {
				games.POST("", server.createGame) // 无认证模式
			}

			// 游戏操作端点
			games.POST("/:id/move", server.playMove)
			games.POST("/:id/pass", server.passTurn)

			if aiClient != nil {
				games.POST("/:id/ai-move", server.aiMove) // AI 落子端点
			}
		}
	}

	server.httpServer = &http.Server{
		Addr:    addr,
		Handler: router,
	}
	return server
}

// Start 启动 HTTP 服务器并处理优雅停机
func (s *Server) Start() error {
	// 在一个 goroutine 中启动服务器, 这样它就不会阻塞主线程
	go func() {
		logger.Info("HTTP server listening", "address", s.httpServer.Addr)
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("HTTP server error", "error", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit // 阻塞在这里, 直到接收到一个信号

	logger.Info("shutting down server...")

	// 创建一个有超时的上下文
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 调用 Shutdown
	if err := s.httpServer.Shutdown(ctx); err != nil {
		logger.Error("server forced to shutdown", "error", err)
		return fmt.Errorf("server forced to shutdown: %w", err)
	}

	logger.Info("server exited gracefully")
	return nil
}

// CreateGameRequest 创建游戏请求
type CreateGameRequest struct {
	IsAIGame bool `json:"is_ai_game"` // 是否为人机对弈
}

// createGame 处理创建新游戏的请求 (POST /v1/games)
func (s *Server) createGame(c *gin.Context) {
	var req CreateGameRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// 如果没有请求体，默认创建等待玩家的游戏
		req.IsAIGame = false
	}

	gameID := uuid.New().String()
	var newGame *game.Game

	// 如果启用了认证，绑定创建者
	if s.userStore != nil && s.jwtManager != nil {
		userID, exists := c.Get("user_id")
		if exists {
			newGame = game.NewGameWithPlayer(userID.(string), req.IsAIGame)
		} else {
			// 未登录用户创建游戏（兼容模式）
			newGame = game.NewGame()
			newGame.IsAIGame = req.IsAIGame
			if req.IsAIGame {
				newGame.PlayerWhite = "AI"
				newGame.Status = game.GameStatusPlaying
			}
		}
	} else {
		// 未启用认证
		newGame = game.NewGame()
		newGame.IsAIGame = req.IsAIGame
		if req.IsAIGame {
			newGame.PlayerWhite = "AI"
			newGame.Status = game.GameStatusPlaying
		}
	}

	if err := s.store.CreateGame(gameID, newGame); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to create game",
		})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"game_id": gameID,
		"state":   newGame,
	})
}

// getGame 获得指定游戏的状态 (GET /v1/games/:id)
func (s *Server) getGame(c *gin.Context) {
	gameID := c.Param("id")

	g, err := s.store.GetGame(gameID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "game not found",
		})
		return
	}

	c.JSON(http.StatusOK, g)
}

// playMove 处理落子请求 (POST /v1/games/:id/move)
func (s *Server) playMove(c *gin.Context) {
	gameID := c.Param("id")

	var moveRequest game.Point
	if err := c.ShouldBindJSON(&moveRequest); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "invalid request body, excepted format: {\"x\": number, \"y\": number}",
		})
		return
	}

	g, err := s.store.GetGame(gameID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "game not found",
		})
		return
	}

	// 如果启用了认证，检查权限
	if s.userStore != nil && s.jwtManager != nil {
		userID, exists := c.Get("user_id")
		if exists {
			// 已登录用户，检查是否有权限落子
			if !g.CanPlayerMove(userID.(string)) {
				c.JSON(http.StatusForbidden, gin.H{
					"error": "not your turn or not a player in this game",
				})
				return
			}
		}
		// 未登录用户可以继续（兼容模式）
	}

	if err := g.PlayMove(moveRequest); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	if err := s.store.UpdateGame(gameID, g); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to updata game state",
		})
		return
	}

	c.JSON(http.StatusOK, g)
}

// passTurn 处理虚手请求 (POST /v1/games/:id/pass)
func (s *Server) passTurn(c *gin.Context) {
	gameID := c.Param("id")

	g, err := s.store.GetGame(gameID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "game not found",
		})
		return
	}

	if err := g.PassTurn(); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	// 更新游戏状态
	if err := s.store.UpdateGame(gameID, g); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to updata game state",
		})
		return
	}

	// 如果游戏结束, 则返回最终得分
	if g.GameOver {
		score, err := g.CalculateScore()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "failed to calculate score",
			})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"message": "game over",
			"state":   g,
			"score":   score,
		})
		return
	}

	c.JSON(http.StatusOK, g)
}

// aiMove 处理 AI 落子请求 (POST /v1/games/:id/ai-move)
func (s *Server) aiMove(c *gin.Context) {
	gameID := c.Param("id")

	// 检查是否配置了 AI 客户端
	if s.aiClient == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": "AI service not configured",
		})
		return
	}

	// 获取游戏状态
	g, err := s.store.GetGame(gameID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "game not found",
		})
		return
	}

	// 检查游戏是否已结束
	if g.GameOver {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "game is over",
		})
		return
	}

	// 调用 AI 服务获取落子
	move, err := s.aiClient.GetMove(g)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": fmt.Sprintf("AI service error: %v", err),
		})
		return
	}

	// 执行落子
	if err := g.PlayMove(move); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": fmt.Sprintf("failed to play AI move: %v", err),
		})
		return
	}

	// 更新游戏状态
	if err := s.store.UpdateGame(gameID, g); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to update game state",
		})
		return
	}

	c.JSON(http.StatusOK, g)
}

// joinGame 处理加入游戏请求 (POST /v1/games/:id/join)
func (s *Server) joinGame(c *gin.Context) {
	gameID := c.Param("id")

	// 获取游戏
	g, err := s.store.GetGame(gameID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "game not found",
		})
		return
	}

	// 获取当前用户 ID
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "authentication required to join game",
		})
		return
	}

	// 加入游戏
	if err := g.JoinGame(userID.(string)); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	// 更新游戏状态
	if err := s.store.UpdateGame(gameID, g); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to update game",
		})
		return
	}

	c.JSON(http.StatusOK, g)
}

// listMyGames 获取当前用户的游戏列表 (GET /v1/games/my)
func (s *Server) listMyGames(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "authentication required",
		})
		return
	}

	games, err := s.store.GetGamesByPlayer(userID.(string))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get games",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"games": games,
		"count": len(games),
	})
}

// listWaitingGames 获取等待玩家加入的游戏列表 (GET /v1/games/waiting)
func (s *Server) listWaitingGames(c *gin.Context) {
	games, err := s.store.GetWaitingGames()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "failed to get waiting games",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"games": games,
		"count": len(games),
	})
}
