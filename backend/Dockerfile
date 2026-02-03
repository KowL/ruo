FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 依赖
COPY backend/requirements.txt* backend/pyproject.toml* backend/uv.lock* ./

# 安装 uv 包管理器和依赖
RUN pip install --no-cache-dir uv && \
    if [ -f pyproject.toml ]; then \
        uv pip install --system -r pyproject.toml || pip install --no-cache-dir -r requirements.txt 2>/dev/null || true; \
    fi

# 安装必要的 Python 包（确保关键依赖）
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    redis \
    celery \
    httpx \
    python-dotenv

# 复制应用代码
COPY backend/app ./app
COPY backend/main.py .
COPY backend/init_database.py .

# 创建必要的目录
RUN mkdir -p /app/cache /app/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
