# 基于 Python 精简镜像
FROM python:3.11-slim

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 安装系统依赖与 Google Chrome
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates apt-transport-https \
    fonts-noto-cjk locales tzdata \
    # Chrome 运行所需依赖
    libasound2 libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 \
    libnss3 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 \
    libglib2.0-0 libgbm1 libpangocairo-1.0-0 libpango-1.0-0 libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/* \
    && echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen

# 添加 Google Chrome 仓库并安装稳定版 Chrome
RUN mkdir -p /etc/apt/keyrings \
    && wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-linux-signing-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 先复制依赖文件并安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 再复制项目代码
COPY . /app

# 入口脚本权限
RUN chmod +x /app/docker-entrypoint.sh

# 以非 root 运行（仍保留 --no-sandbox 以提升兼容性）
RUN useradd -ms /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# 运行
ENTRYPOINT ["/app/docker-entrypoint.sh"]
