# 基于 Python 精简镜像
FROM python:3.11-slim

# 环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai

# 安装必要的系统依赖（不再在应用容器内安装 Chrome/Driver）
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates unzip \
    fonts-noto-cjk locales tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen

## 不再需要在应用容器内指定 CHROME_BIN（使用远程 Selenium）

# 创建工作目录
WORKDIR /app

# 先复制依赖文件并安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 再复制项目代码
COPY . /app

# 入口脚本权限
RUN chmod +x /app/docker-entrypoint.sh

# 运行
ENTRYPOINT ["/app/docker-entrypoint.sh"]
