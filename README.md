# Discord to WeChat

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
- 如使用企业微信，填写 `ENTERPRISE_WECHAT_WEBHOOK`
- 如使用微信个人号，填写 `WECHAT_RECEIVER_NAME`

### 2. 启动方式

#### 方式一：本地启动

**前置要求**：
- Python 3.8+
- Chrome 浏览器

**步骤**：

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python discord_to_wechat.py
```

首次运行会打开浏览器窗口，需要手动登录 Discord。

---

#### 方式二：Docker 启动（推荐）

**前置要求**：
- Docker & Docker Compose

**步骤**：

1. **初始化数据目录**

```bash
bash bash/init_selenium.sh
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **首次登录 Discord**

打开浏览器访问 noVNC：

```
http://localhost:7900
```

- 默认密码：`secret`
- 在 noVNC 页面中打开浏览器，访问 Discord 并登录
- 登录成功后，数据会自动保存到 `selenium_data` 目录
- 后续重启无需再次登录

4. **查看日志**

```bash
docker-compose logs -f discord-to-wechat
```

5. **停止服务**

```bash
docker-compose down
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

