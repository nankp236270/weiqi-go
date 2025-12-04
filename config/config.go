package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

// Config 结构体用于存放从环境变量加载的所有配置项
type Config struct {
	MongoURI       string
	DBName         string
	CollectionName string
	UserCollection string
	ServerPort     string
	AIServiceURL   string
	JWTSecret      string
	LogLevel       string
	LogJSON        bool
}

// LoadConfig 加载 .env 问卷和环境变量, 并返回一个 Config 结构体
func LoadConfig() *Config {
	// 在非生产环境中加载 .env 文件
	if os.Getenv("GIN_MODE") != "release" {
		if err := godotenv.Load(); err != nil {
			log.Println("No .env file found, using environment variables")
		}
	}

	cfg := &Config{
		MongoURI:       getEnv("MONGO_URI", ""),
		DBName:         getEnv("DB_NAME", "weiqi"),
		CollectionName: getEnv("COLLECTION_NAME", "games"),
		UserCollection: getEnv("USER_COLLECTION", "users"),
		ServerPort:     getEnv("SERVER_PORT", "8080"),
		AIServiceURL:   getEnv("AI_SERVICE_URL", ""),
		JWTSecret:      getEnv("JWT_SECRET", ""),
		LogLevel:       getEnv("LOG_LEVEL", "info"),
		LogJSON:        getEnv("LOG_JSON", "false") == "true",
	}

	if cfg.MongoURI == "" {
		log.Fatal("MONGO_URI environment variable is required")
	}

	if cfg.JWTSecret == "" {
		log.Println("Warning: JWT_SECRET not set, using default (insecure for production)")
		cfg.JWTSecret = "default-secret-change-in-production"
	}

	return cfg
}

// getEnv 是一个辅助函数, 用于读取环境变量, 如果不存在则返回一个默认值
func getEnv(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return fallback
}
