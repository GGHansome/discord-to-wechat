# 消息发送方式配置
# 可选值:
#   "wechat"             - 微信个人号（需要小号扫码登录，发送给大号）
#   "enterprise_wechat"  - 企业微信机器人（使用Webhook，发送到企业微信群）
SENDER_TYPE = "enterprise_wechat"  # 默认使用微信个人号

# Discord配置
# 可以配置多个频道URL，程序会轮询监听所有频道
DISCORD_CHANNEL_URLS = [
    # 在这里添加更多频道，例如：
    # "https://discord.com/channels/服务器ID/频道ID",
]

# 微信个人号配置（当 SENDER_TYPE = "wechat" 时使用）
WECHAT_RECEIVER_NAME = ""  # 你大号在小号中的备注名或昵称


# 企业微信机器人配置（当 SENDER_TYPE = "enterprise_wechat" 时使用）
# 获取方式：
# 1. 在企业微信群中，点击群设置 -> 群机器人 -> 添加机器人
# 2. 复制机器人的 Webhook 地址到下方

# 旧版配置（单个Webhook，所有频道消息都发到这里）
# ENTERPRISE_WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=abcde"

# 新版配置（多Webhook映射，不同频道发到不同群）
# 格式: [{'hook': 'Webhook地址', 'channel': 'Discord频道URL'}]
ENTERPRISE_WECHAT_WEBHOOK_LIST = [
    # {
    #     'hook': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx',
    #     'channel': 'https://discord.com/channels/123456789/987654321'
    # },
    # {
    #     'hook': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=yyyyy',
    #     'channel': 'https://discord.com/channels/123456789/123456789'
    # }
]


# 运行配置
# 监控间隔（秒）
CHECK_INTERVAL = 30

# Chrome配置
HEADLESS_MODE = False  # 设为True则无头模式（不显示浏览器窗口）
