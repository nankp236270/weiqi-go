package logger

import (
	"context"
	"log/slog"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

// Logger 全局日志实例
var Logger *slog.Logger

// LogLevel 日志级别
type LogLevel string

const (
	LevelDebug LogLevel = "debug"
	LevelInfo  LogLevel = "info"
	LevelWarn  LogLevel = "warn"
	LevelError LogLevel = "error"
)

// Config 日志配置
type Config struct {
	Level      LogLevel
	JSONFormat bool
	AddSource  bool
}

// Init 初始化日志系统
func Init(cfg Config) {
	var level slog.Level
	switch cfg.Level {
	case LevelDebug:
		level = slog.LevelDebug
	case LevelInfo:
		level = slog.LevelInfo
	case LevelWarn:
		level = slog.LevelWarn
	case LevelError:
		level = slog.LevelError
	default:
		level = slog.LevelInfo
	}

	opts := &slog.HandlerOptions{
		Level:     level,
		AddSource: cfg.AddSource,
	}

	var handler slog.Handler
	if cfg.JSONFormat {
		handler = slog.NewJSONHandler(os.Stdout, opts)
	} else {
		handler = slog.NewTextHandler(os.Stdout, opts)
	}

	Logger = slog.New(handler)
	slog.SetDefault(Logger)
}

// WithRequestID 添加请求 ID 到上下文
func WithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, "request_id", requestID)
}

// GetRequestID 从上下文获取请求 ID
func GetRequestID(ctx context.Context) string {
	if requestID, ok := ctx.Value("request_id").(string); ok {
		return requestID
	}
	return ""
}

// Info 记录 Info 级别日志
func Info(msg string, args ...any) {
	Logger.Info(msg, args...)
}

// Debug 记录 Debug 级别日志
func Debug(msg string, args ...any) {
	Logger.Debug(msg, args...)
}

// Warn 记录 Warn 级别日志
func Warn(msg string, args ...any) {
	Logger.Warn(msg, args...)
}

// Error 记录 Error 级别日志
func Error(msg string, args ...any) {
	Logger.Error(msg, args...)
}

// InfoContext 记录带上下文的 Info 日志
func InfoContext(ctx context.Context, msg string, args ...any) {
	if requestID := GetRequestID(ctx); requestID != "" {
		args = append(args, "request_id", requestID)
	}
	Logger.InfoContext(ctx, msg, args...)
}

// ErrorContext 记录带上下文的 Error 日志
func ErrorContext(ctx context.Context, msg string, args ...any) {
	if requestID := GetRequestID(ctx); requestID != "" {
		args = append(args, "request_id", requestID)
	}
	Logger.ErrorContext(ctx, msg, args...)
}

// RequestLoggerMiddleware Gin 请求日志中间件
func RequestLoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		// 生成请求 ID
		requestID := generateRequestID()
		c.Set("request_id", requestID)

		// 记录请求开始
		Logger.Info("request started",
			"request_id", requestID,
			"method", c.Request.Method,
			"path", path,
			"query", query,
			"ip", c.ClientIP(),
			"user_agent", c.Request.UserAgent(),
		)

		// 处理请求
		c.Next()

		// 记录请求结束
		duration := time.Since(start)
		status := c.Writer.Status()

		logLevel := slog.LevelInfo
		if status >= 500 {
			logLevel = slog.LevelError
		} else if status >= 400 {
			logLevel = slog.LevelWarn
		}

		Logger.Log(c.Request.Context(), logLevel, "request completed",
			"request_id", requestID,
			"method", c.Request.Method,
			"path", path,
			"status", status,
			"duration_ms", duration.Milliseconds(),
			"ip", c.ClientIP(),
		)
	}
}

// generateRequestID 生成唯一的请求 ID
func generateRequestID() string {
	return time.Now().Format("20060102150405") + "-" + randomString(8)
}

// randomString 生成随机字符串
func randomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyz0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[time.Now().UnixNano()%int64(len(letters))]
	}
	return string(b)
}

