# 多阶段构建 - 构建阶段
FROM golang:1.25.3-alpine AS builder

# 安装必要的工具
RUN apk add --no-cache git

WORKDIR /app

# 复制 go mod 文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o weiqi-go-server .

# 运行阶段 - 使用更小的镜像
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 从构建阶段复制编译好的二进制文件
COPY --from=builder /app/weiqi-go-server .

# 暴露端口
EXPOSE 8080

# 运行应用
CMD ["./weiqi-go-server"]

