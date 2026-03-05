FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/pyproject.toml backend/uv.lock* ./

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv

# 安装项目依赖
RUN if [ -f pyproject.toml ]; then \
    uv pip install --system --no-cache . ; \
    fi

# 复制应用代码
COPY backend/app ./app
COPY backend/main.py .


# 创建必要的目录
RUN mkdir -p /app/cache /app/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
