# Cloudflare DDNS 自动更新脚本

本项目用于自动检测本机公网IP变化，并通过Cloudflare API自动更新指定域名的A记录，同时支持通过Telegram Bot推送更新通知。

## 功能简介
- 自动检测公网IP变化
- 自动更新Cloudflare DNS记录
- 支持Telegram消息通知
- 所有配置集中于.env文件

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置.env文件

在本目录下复制并编辑 `.env` 文件，填写如下内容：

```env
# Cloudflare 配置
CF_API_TOKEN=你的Cloudflare API Token
CF_ZONE_ID=你的Zone ID
CF_RECORD_ID=你的DNS记录ID
CF_RECORD_NAME=你的域名（如 ddns.example.com）

# Telegram 配置
TELEGRAM_BOT_TOKEN=你的TG Bot Token
TELEGRAM_CHAT_ID=你的TG Chat ID
```

- 如何获取 `CF_ZONE_ID` 和 `CF_RECORD_ID` 可参考 [Cloudflare官方文档](https://api.cloudflare.com/)

CF_ZONE_ID（域名的区域ID）
curl.exe -X GET "https://api.cloudflare.com/client/v4/zones?name=example.com" -H "Authorization: Bearer 你的Cloudflare API Token" -H "Content-Type: application/json"

CF_RECORD_ID（先dns解析，再运行）
curl.exe -X GET "https://api.cloudflare.com/client/v4/zones/288f55b60b96dad364ff464c1ccbbc0b/dns_records?name=ddns.example.com" -H "Authorization: Bearer 你的Cloudflare API Token" -H "Content-Type: application/json"

以上两个获取的命令直接在本地使用powershell运行即可！

### 3. 运行脚本

```bash
python cf_ddns.py
```

建议将脚本加入定时任务（如Windows任务计划、Linux crontab）实现定时自动检测。

## 注意事项
- 请确保API Token具备Zone DNS编辑权限。
- Telegram通知为可选功能，若不需要可留空相关配置。

## License
MIT