FROM python:3.11-slim

WORKDIR /app

# 复制依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 MDK 核心知识库
COPY ../../core /app/mdk/core

# 复制 MCP Server
COPY server.py .

# 环境变量
ENV MDK_CORE_DIR=/app/mdk/core
ENV PYTHONUNBUFFERED=1

EXPOSE 8765

CMD ["python", "server.py"]
