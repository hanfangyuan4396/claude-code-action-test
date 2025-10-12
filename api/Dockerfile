FROM python:3.12-slim-bookworm

WORKDIR /api

# 安装 curl（用于健康检查）并精简依赖
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

RUN chmod +x /api/bin/boot.sh

EXPOSE 8000

ENTRYPOINT ["/api/bin/boot.sh"]
