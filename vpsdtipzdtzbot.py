import requests
import asyncio
from telegram import Bot

BOT_TOKEN = "你的Bot Token"    # 使用 https://t.me/BotFather 创建获取你的 Bot Token
CHAT_ID = "你的Telegram ID"    # 使用 https://t.me/nmnmfunbot 输入 /id 获取你的 Telegram ID
CHECK_INTERVAL = 300  # 秒 # 检查间隔时间，默认每5分钟检查一次

bot = Bot(token=BOT_TOKEN)
last_ip = None

async def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return None

async def check_ip_loop():
    global last_ip
    while True:
        current_ip = await get_public_ip()
        if current_ip:
            if current_ip != last_ip:
                message = f"🔔 公网 IP 发生变化：\n旧 IP: {last_ip}\n新 IP: {current_ip}" if last_ip else f"🔔 当前公网 IP：{current_ip}"
                await bot.send_message(chat_id=CHAT_ID, text=message)
                last_ip = current_ip
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(check_ip_loop())
