.PHONY: help build test run clean docker-build docker-up docker-down docker-logs deploy test-api logs logs-json logs-errors

# 默认目标
help:
	@echo "Weiqi-Go 项目管理命令:"
	@echo ""
	@echo "开发命令:"
	@echo "  make build        - 编译 Go 项目"
	@echo "  make test         - 运行所有测试"
	@echo "  make run          - 本地运行服务器"
	@echo "  make clean        - 清理编译产物"
	@echo ""
	@echo "Docker 命令:"
	@echo "  make docker-build - 构建 Docker 镜像"
	@echo "  make docker-up    - 启动所有容器"
	@echo "  make docker-down  - 停止所有容器"
	@echo "  make docker-logs  - 查看容器日志"
	@echo ""
	@echo "部署命令:"
	@echo "  make deploy       - 完整部署（构建+启动+测试）"
	@echo "  make test-api     - 测试 API 端点"
	@echo ""
	@echo "日志命令:"
	@echo "  make logs         - 查看实时日志"
	@echo "  make logs-json    - 查看 JSON 格式日志"
	@echo "  make logs-errors  - 查看错误日志"

# 编译 Go 项目
build:
	@echo "🔨 编译 Go 项目..."
	go build -o weiqi-go-server .
	@echo "✅ 编译完成"

# 运行所有测试
test:
	@echo "🧪 运行 Go 测试..."
	go test ./... -v -cover
	@echo ""
	@echo "🧪 运行 Python 测试..."
	cd weiqi-ai && python3 test_simple.py

# 本地运行服务器
run:
	@echo "▶️  启动服务器..."
	go run main.go

# 清理编译产物
clean:
	@echo "🧹 清理编译产物..."
	rm -f weiqi-go-server
	go clean
	@echo "✅ 清理完成"

# 构建 Docker 镜像
docker-build:
	@echo "🔨 构建 Docker 镜像..."
	docker compose build

# 启动所有容器
docker-up:
	@echo "▶️  启动所有容器..."
	docker compose up -d
	@echo "✅ 容器已启动"
	@echo ""
	@make docker-ps

# 停止所有容器
docker-down:
	@echo "🛑 停止所有容器..."
	docker compose down

# 查看容器日志
docker-logs:
	docker compose logs -f

# 查看容器状态
docker-ps:
	@echo "📦 容器状态:"
	@docker compose ps

# 完整部署
deploy:
	@./scripts/deploy.sh

# 测试 API
test-api:
	@./scripts/test-api.sh

# 开发模式（热重载）
dev:
	@echo "🔥 开发模式（需要安装 air）..."
	@if command -v air > /dev/null; then \
		air; \
	else \
		echo "❌ 未安装 air，使用普通模式..."; \
		echo "💡 安装 air: go install github.com/air-verse/air@latest"; \
		go run main.go; \
	fi

# 查看 Go 依赖
deps:
	@echo "📦 Go 依赖:"
	go list -m all

# 更新依赖
update-deps:
	@echo "⬆️  更新依赖..."
	go get -u ./...
	go mod tidy

# 格式化代码
fmt:
	@echo "🎨 格式化代码..."
	go fmt ./...
	@echo "✅ 格式化完成"

# 代码检查
lint:
	@echo "🔍 代码检查..."
	@if command -v golangci-lint > /dev/null; then \
		golangci-lint run; \
	else \
		echo "⚠️  未安装 golangci-lint"; \
		echo "💡 安装: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"; \
	fi

# 查看实时日志（文本格式）
logs:
	@echo "📝 查看实时日志..."
	@docker compose logs -f weiqi-backend

# 查看 JSON 格式日志
logs-json:
	@echo "📊 查看 JSON 格式日志..."
	@docker compose logs weiqi-backend --no-log-prefix | grep -E '^\{' | jq '.'

# 查看错误日志
logs-errors:
	@echo "⚠️  查看错误日志..."
	@docker compose logs weiqi-backend --no-log-prefix | grep -E 'level=(ERROR|WARN)|"level":"(ERROR|WARN)"'

