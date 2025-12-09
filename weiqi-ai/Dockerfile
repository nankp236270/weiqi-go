FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（这层会被缓存，除非 requirements.txt 改变）
RUN pip install --no-cache-dir -r requirements.txt

# 只复制运行 API 服务需要的代码文件
# 注意：不复制 models/, venv/, logs/ 等大文件
COPY ai/ ./ai/
COPY api/ ./api/
COPY core/ ./core/
COPY training/ ./training/

# 环境变量配置
ENV AI_MODE=pure_mcts
ENV NUM_SIMULATIONS=400
ENV SCORING_MODE=monte_carlo
ENV SCORING_SIMULATIONS=200

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
