package main

import (
	"fmt"
	"time"

	"github.com/nankp236270/weiqi-go/ai"
	"github.com/nankp236270/weiqi-go/api"
	"github.com/nankp236270/weiqi-go/auth"
	"github.com/nankp236270/weiqi-go/config"
	"github.com/nankp236270/weiqi-go/database"
	"github.com/nankp236270/weiqi-go/logger"
	"github.com/nankp236270/weiqi-go/storage"
	"github.com/nankp236270/weiqi-go/user"
)

func main() {
	// 1. 加载 .env 文件
	cfg := config.LoadConfig()

	// 2. 初始化日志系统
	logger.Init(logger.Config{
		Level:      logger.LogLevel(cfg.LogLevel),
		JSONFormat: cfg.LogJSON,
		AddSource:  false,
	})
	logger.Info("application starting",
		"version", "1.0.0",
		"log_level", cfg.LogLevel,
		"log_format", map[bool]string{true: "json", false: "text"}[cfg.LogJSON],
	)

	// 3. 连接数据库 (并获取清理函数)
	logger.Info("connecting to database", "uri", cfg.MongoURI)
	mongoClient, cleanup := database.Connect(cfg)
	defer cleanup() // 确保程序退出时关闭连接
	logger.Info("database connected successfully")

	// 4. 初始化存储层
	gameCollection := mongoClient.Database(cfg.DBName).Collection(cfg.CollectionName)
	store := storage.NewMongoGameStore(gameCollection)
	logger.Info("game store initialized", "collection", cfg.CollectionName)

	// 初始化用户存储
	userCollection := mongoClient.Database(cfg.DBName).Collection(cfg.UserCollection)
	userStore := user.NewMongoUserStore(userCollection)
	logger.Info("user store initialized", "collection", cfg.UserCollection)

	// 初始化 JWT 管理器
	jwtManager := auth.NewJWTManager(cfg.JWTSecret, 24*time.Hour) // Token 有效期 24 小时
	logger.Info("JWT authentication enabled", "token_duration", "24h")

	// 5. 初始化 AI 客户端（如果配置了）
	var aiClient *ai.Client
	if cfg.AIServiceURL != "" {
		aiClient = ai.NewClient(cfg.AIServiceURL)
		logger.Info("AI service configured", "url", cfg.AIServiceURL)

		// 检查 AI 服务健康状态
		if err := aiClient.HealthCheck(); err != nil {
			logger.Warn("AI service health check failed", "error", err)
			logger.Warn("AI features will be unavailable")
			aiClient = nil
		} else {
			logger.Info("AI service is healthy")
		}
	} else {
		logger.Info("AI service not configured")
	}

	// 6. 初始化并启动 API 服务器
	addr := fmt.Sprintf(":%s", cfg.ServerPort)
	server := api.NewServerWithAuth(addr, store, userStore, aiClient, jwtManager)

	logger.Info("server configured",
		"port", cfg.ServerPort,
		"game_storage", "MongoDB",
		"user_auth", "Enabled",
		"ai_service", map[bool]string{true: "Enabled", false: "Disabled"}[aiClient != nil],
	)

	// Start 会阻塞直到服务器被关闭
	logger.Info("starting HTTP server", "address", addr)
	if err := server.Start(); err != nil {
		logger.Error("server error", "error", err)
	}

	// 当 Start 返回后, main 函数结束, defer cleanup 会被调用
	logger.Info("application gracefully shut down")
}
