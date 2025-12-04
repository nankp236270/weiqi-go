# 🚀 围棋对弈平台 - Docker 部署说明

**更新时间**: 2025年12月4日

---

## 📦 容器化部署

所有服务（包括前端）已完全容器化，使用 Docker Compose 一键部署。

---

## 🌐 端口映射

### 对外开放端口

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| **前端** | 80 | **30000** | 用户访问入口 ⭐ |
| 后端 API | 8080 | 8080 | RESTful API（可选） |
| AI 服务 | 8000 | 8000 | AI 服务（内部） |
| MongoDB | 27017 | 27017 | 数据库（不应暴露） |

### 推荐配置

**只需要开放端口 30000！**

前端会通过 nginx 代理自动转发 API 请求到后端，无需暴露后端端口。

---

## 🚀 快速部署

### 1. 启动所有服务

```bash
cd /home/zhuji/weiqi-go
docker compose up -d --build
```

### 2. 查看服务状态

```bash
docker ps
```

预期输出：
```
NAMES              STATUS         PORTS
weiqi-frontend     Up             0.0.0.0:30000->80/tcp
weiqi-backend      Up             0.0.0.0:8080->8080/tcp
weiqi-ai           Up (healthy)   0.0.0.0:8000->8000/tcp
weiqi-mongo        Up (healthy)   0.0.0.0:27017->27017/tcp
```

### 3. 访问网站

```
http://你的服务器IP:30000
```

---

## 📋 服务架构

```
用户浏览器
    ↓
端口 30000 (前端 nginx)
    ↓
    ├─→ 静态文件 (Vue.js 构建产物)
    └─→ /v1/* API 请求 → 端口 8080 (后端)
                            ↓
                        端口 8000 (AI 服务)
                            ↓
                        端口 27017 (MongoDB)
```

---

## 🔧 配置文件

### Docker Compose

**文件**: `docker-compose.yml`

```yaml
services:
  weiqi-frontend:
    build:
      context: ./weiqi-frontend
      dockerfile: Dockerfile
    container_name: weiqi-frontend
    ports:
      - "30000:80"  # 主机端口:容器端口
    networks:
      - weiqi-network
    depends_on:
      - weiqi-backend
    restart: unless-stopped
```

### Nginx 配置

**文件**: `weiqi-frontend/nginx.conf`

```nginx
server {
    listen 80;
    
    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理到后端
    location /v1/ {
        proxy_pass http://weiqi-backend:8080;
    }
}
```

---

## 🛠️ 常用命令

### 启动服务
```bash
docker compose up -d
```

### 停止服务
```bash
docker compose down
```

### 重新构建并启动
```bash
docker compose up -d --build
```

### 查看日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f weiqi-frontend
docker compose logs -f weiqi-backend
docker compose logs -f weiqi-ai
```

### 重启特定服务
```bash
docker compose restart weiqi-frontend
```

---

## 🔒 生产环境建议

### 1. 使用反向代理（推荐）

使用 Nginx 或 Caddy 作为反向代理，配置 HTTPS：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:30000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 2. 防火墙配置

```bash
# 只开放必要的端口
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 30000/tcp # 围棋平台（如果直接访问）

# 不要开放这些端口
# ufw deny 8080/tcp   # 后端 API
# ufw deny 8000/tcp   # AI 服务
# ufw deny 27017/tcp  # MongoDB
```

### 3. 环境变量

创建 `.env` 文件：

```bash
MONGO_USER=your_mongo_user
MONGO_PASS=your_strong_password
DB_NAME=weiqi
COLLECTION_NAME=games
SERVER_PORT=8080
```

### 4. 数据备份

```bash
# 备份 MongoDB 数据
docker exec weiqi-mongo mongodump --out /backup

# 导出容器中的备份
docker cp weiqi-mongo:/backup ./mongodb-backup
```

---

## 📊 性能优化

### 1. 前端优化

前端已配置：
- ✅ Gzip 压缩
- ✅ 静态资源缓存（1年）
- ✅ 生产环境构建优化

### 2. 容器资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  weiqi-frontend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## 🐛 故障排查

### 前端无法访问

```bash
# 检查容器状态
docker ps | grep weiqi-frontend

# 查看日志
docker logs weiqi-frontend

# 检查端口占用
netstat -tulpn | grep 30000
```

### API 请求失败

```bash
# 检查后端容器
docker logs weiqi-backend

# 进入前端容器测试连接
docker exec -it weiqi-frontend sh
wget -O- http://weiqi-backend:8080/health
```

### 容器无法启动

```bash
# 查看详细错误
docker compose logs

# 清理并重新构建
docker compose down -v
docker compose up -d --build
```

---

## 📝 更新部署

### 更新代码后重新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建并启动
docker compose up -d --build

# 3. 验证服务
docker ps
curl http://localhost:30000
```

---

## 🎯 端口总结

### 对外访问
- **端口 30000**: 用户访问围棋平台 ⭐

### 内部通信（不需要暴露）
- 端口 8080: 后端 API（通过前端代理）
- 端口 8000: AI 服务（后端内部调用）
- 端口 27017: MongoDB（后端内部调用）

---

## ✅ 部署检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] `.env` 文件已配置
- [ ] 端口 30000 未被占用
- [ ] 防火墙已配置（如需要）
- [ ] 所有容器正常运行
- [ ] 可以访问 http://localhost:30000
- [ ] 可以注册和登录
- [ ] 可以创建和加入游戏

---

**🎉 部署完成！访问 http://你的IP:30000 开始使用围棋对弈平台！**

