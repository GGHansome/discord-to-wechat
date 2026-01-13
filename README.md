## Discord to WeChat

Discord 消息转发工具，支持转发到微信个人号或企业微信群机器人。

## 快速开始

### 1. 配置

复制配置文件并修改：

```bash
cp config.example.py config.py
```

编辑 `config.py`：
- 添加 Discord 频道 URL 到 `DISCORD_CHANNEL_URLS`
- 选择发送方式 `SENDER_TYPE`（`wechat` 或 `enterprise_wechat`）
- 如使用企业微信，填写 `ENTERPRISE_WECHAT_WEBHOOK` 或 `ENTERPRISE_WECHAT_WEBHOOK_LIST`
- 如使用微信个人号，填写 `WECHAT_RECEIVER_NAME`

### 2. 启动方式（3种）

#### 方式一：本地启动（Python 直接运行）

**前置要求**：
- Python 3.8+
- Chrome 浏览器
- chromedriver（需与本机 Chrome 版本匹配，并确保在 PATH 中；或设置 `CHROMEDRIVER_PATH` 指向可执行文件）

**步骤**：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python discord_to_wechat.py
```

首次运行会打开浏览器窗口，需要手动登录 Discord。

如果启动时报 `Unable to locate or obtain driver for chrome`，说明 Selenium 没有拿到驱动：
- 先检查：`which chromedriver`
- 或指定：`export CHROMEDRIVER_PATH=/path/to/chromedriver`
- 或直接使用下方 Docker 方式（推荐），避免本地驱动/版本匹配问题

---

#### 方式二：本地 Docker 启动（Mac/Windows 推荐）

**前置要求**：
- Docker & Docker Compose

**步骤**：

1. **初始化数据目录**

```bash
bash bash/init_selenium.sh
```

2. **启动服务**

```bash
docker compose up -d --build
```

3. **首次登录 Discord（通过 noVNC）**

打开浏览器访问 noVNC：`http://localhost:7900`

- 默认密码：`secret`
- 在 noVNC 页面中打开浏览器，访问 Discord 并登录
- 登录成功后，数据会自动保存到 `selenium_data` 目录
- 后续重启无需再次登录

4. **查看日志**

```bash
docker compose logs -f discord-to-wechat
```

5. **停止服务**

```bash
docker compose down
```

**说明（为什么本地不用 host 网络）**：
- `docker-compose.yml` 使用默认 bridge 网络并通过 `ports` 暴露 noVNC（`http://localhost:7900`）。
- 在 macOS 的 Docker Desktop 上不建议使用 `network_mode: host`（行为不等价于 Linux，且容易导致 `ports:` 映射不可用）。

---

#### 方式三：服务器 Docker 启动（Linux 部署）

**适用场景**：部署到 Linux 服务器长期运行；服务器可能开了透明代理（v2ray 等）或只提供 HTTP(S) 代理环境变量。

**步骤**：

1. **初始化数据目录（首次部署）**

```bash
bash bash/init_selenium.sh
```

2. **选择一种网络模式启动**

- **A. 服务器是透明代理（v2ray / TUN / iptables）并希望容器直接复用宿主网络**（推荐这种场景）：

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.yml up -d --build
```

说明：
- `docker-compose.linux.yml` 会把服务切到 `network_mode: host`（Linux 才等价好用）。
- noVNC/selenium 端口会直接在宿主机监听：确保服务器防火墙放行 `7900/4444`。

- **B. 服务器是 HTTP(S)PROXY 环境变量代理**（不走透明代理）：

你需要让 **Selenium 里的 Chrome** 也走代理。本项目会在创建远程 Chrome 时读取 `CHROME_PROXY`（优先）或 `HTTPS_PROXY/HTTP_PROXY` 并注入 `--proxy-server=...`。

做法：在 `docker-compose.yml` 的 `discord-to-wechat.environment` 里配置（示例）：
- `CHROME_PROXY=http://127.0.0.1:7890`（或你的代理地址）
- `NO_PROXY=selenium,localhost,127.0.0.1`（关键：避免 WebDriver 连接 selenium 也走代理）

然后按方式二启动即可：

```bash
docker compose up -d --build
```

## 常见问题 (FAQ)

### 1. Docker 启动报错 `SessionNotCreatedException: Chrome instance exited`

**场景**：通常发生在**首次登录成功并重启服务后**（即第二次启动时）。

如果遇到类似以下的报错：

```text
org.openqa.selenium.SessionNotCreatedException: Could not start a new session. Response code 500. Message: session not created: Chrome instance exited. Examine ChromeDriver verbose log to determine the cause.
...
Driver info: driver.version: unknown
```

**原因**：通常是因为 `selenium_data` 目录权限问题，或者上次异常退出导致残留了 Chrome 的锁文件（`SingletonLock` 等）。

**解决方法**：

运行初始化脚本以修复权限并清理锁文件：

```bash
bash bash/init_selenium.sh
```

然后重启容器：
```bash
docker compose restart
```

## 说明

- Docker 方式使用 Selenium 无头浏览器，通过 noVNC 提供远程访问
- 首次登录后，Discord 会话会持久化保存
- 监控间隔可在 `config.py` 中的 `CHECK_INTERVAL` 调整
- 微信个人号需要扫码登录（建议使用小号转发到大号）

## 目录结构

```
.
├── config.py              # 配置文件（需手动创建）
├── discord_to_wechat.py   # 主程序
├── docker-compose.yml     # Docker 配置
├── bash/
│   └── init_selenium.sh   # 初始化脚本
└── selenium_data/         # Docker 持久化数据（首次运行后生成）
```
