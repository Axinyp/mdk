# 构建命令（从 mdk/ 根目录执行）:
#   docker build -f adapters/mcp-server/Dockerfile -t mdk-mcp-server .
#
# 运行:
#   docker run -i mdk-mcp-server

FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY adapters/mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 MDK 核心知识库（从 mdk/ 根目录的 core/）
COPY core /app/core

# 复制 MCP Server
COPY adapters/mcp-server/server.py .

ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
