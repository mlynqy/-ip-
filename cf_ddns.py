import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

load_dotenv()

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ZONE_ID = os.getenv("CF_ZONE_ID")
CF_RECORD_ID = os.getenv("CF_RECORD_ID")
CF_RECORD_NAME = os.getenv("CF_RECORD_NAME")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CF_API_BASE = "https://api.cloudflare.com/client/v4"

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except Exception as e:
        print(f"获取公网IP失败: {e}")
        return None

def get_dns_record_ip():
    url = f"{CF_API_BASE}/zones/{CF_ZONE_ID}/dns_records/{CF_RECORD_ID}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.json()["result"]["content"]
    else:
        print(f"获取DNS记录失败: {resp.text}")
        return None

def update_dns_record(new_ip):
    url = f"{CF_API_BASE}/zones/{CF_ZONE_ID}/dns_records/{CF_RECORD_ID}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    data = {"type": "A", "name": CF_RECORD_NAME, "content": new_ip, "ttl": 1, "proxied": False}
    resp = requests.put(url, headers=headers, json=data)
    return resp.ok

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram通知失败: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(TELEGRAM_CHAT_ID):
        await update.message.reply_text("无权限。请联系管理员绑定chat_id。")
        return
    await update.message.reply_text(
        "欢迎使用 Cloudflare DDNS Bot！\n\n" \
        "可用命令：\n" \
        "/ip - 获取当前公网IP和DNS记录IP\n" \
        "/start - 显示本帮助信息"
    )

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(TELEGRAM_CHAT_ID):
        await update.message.reply_text("无权限。请联系管理员绑定chat_id。")
        return
    public_ip = get_public_ip()
    dns_ip = get_dns_record_ip()
    # 查询IP详细信息
    asn = country = org = isp_type = "-"
    try:
        resp = requests.get(f"https://ipinfo.io/{public_ip}/json", timeout=5)
        if resp.ok:
            data = resp.json()
            asn = data.get("org", "-")
            country = data.get("country", "-")
            org = data.get("org", "-")
            # 判断是否为家宽ISP（简单判断：org/org字段包含 'CHINANET', 'UNICOM', 'MOBILE', 'BROADBAND', 'TELECOM', '家庭', 'ISP' 等关键词）
            isp_keywords = ["CHINANET", "UNICOM", "MOBILE", "BROADBAND", "TELECOM", "家庭", "ISP"]
            isp_type = "yes" if any(k.lower() in org.lower() for k in isp_keywords) else "no"
    except Exception as e:
        pass
    msg = (
        f"当前公网IP: {public_ip}\n"
        f"DNS记录IP: {dns_ip}\n"
        f"ASN: {asn}\n"
        f"国家: {country}\n"
        f"所属企业: {org}\n"
        f"ISP: {isp_type}\n"
        f"来源于ipify.org"
    )
    await update.message.reply_text(msg)

def main():
    # DDNS自动检测逻辑
    public_ip = get_public_ip()
    if public_ip:
        dns_ip = get_dns_record_ip()
        if dns_ip and public_ip != dns_ip:
            if update_dns_record(public_ip):
                send_telegram_message(f"Cloudflare DDNS更新成功: {CF_RECORD_NAME} -> {public_ip}")
                print(f"DNS记录已更新: {public_ip}")
            else:
                send_telegram_message(f"Cloudflare DDNS更新失败: {CF_RECORD_NAME}")
                print("DNS记录更新失败")
        else:
            print("IP未变化，无需更新")
    # 启动Telegram命令Bot
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("ip", ip))
        print("Telegram命令Bot已启动...")
        asyncio.run(app.run_polling())

if __name__ == "__main__":
    main()