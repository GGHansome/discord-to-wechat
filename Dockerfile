# 基于 Python 精简镜像
FROM python:3.11-slim

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 安装系统依赖与发行版 Chromium（APT 会自动拉取所需依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates unzip \
    fonts-noto-cjk locales tzdata \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/* \
    && echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen

# 指定系统 Chromium 可执行路径，避免某些环境下探测失败
ENV CHROME_BIN=/usr/bin/chromium

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
