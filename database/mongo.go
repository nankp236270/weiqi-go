package database

import (
	"context"
	"time"

	"github.com/nankp236270/weiqi-go/config"
	"github.com/nankp236270/weiqi-go/logger"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Connect 函数负责初始化并返回一个 MongoDB 客户端
// 它还返回一个 cleanup 函数, 用于在程序结束时安全地断开连接
func Connect(cfg *config.Config) (*mongo.Client, func()) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	logger.Debug("attempting to connect to MongoDB", "uri", cfg.MongoURI)
	
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(cfg.MongoURI))
	if err != nil {
		logger.Error("failed to connect to MongoDB", "error", err)
		panic(err)
	}

	// 定义一个清理函数, 用于关闭连接
	cleanup := func() {
		logger.Info("closing MongoDB connection...")
		if err := client.Disconnect(context.Background()); err != nil {
			logger.Error("failed to disconnect MongoDB client", "error", err)
		} else {
			logger.Info("MongoDB connection closed")
		}
	}

	return client, cleanup
}
