import asyncio
import aiohttp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

BOT_TOKEN = "7841136579:AAEvrOsxKv-M04w5dtJF9gXBKTEefZyceA0"
CHAT_ID = "6440088895"
CHECK_INTERVAL = 300  # 秒
last_ip = None

async def get_public_ip():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.ipify.org") as resp:
                return (await resp.text()).strip()
    except Exception as e:
        print(f"❌ 获取 IP 失败: {e}")
        return None

async def check_ip_loop(app):
    global last_ip
    bot = app.bot
    while True:
        current_ip = await get_public_ip()
        if current_ip and current_ip != last_ip:
            text = f"🔔 公网 IP 发生变化：\n旧 IP: {last_ip}\n新 IP: {current_ip}" if last_ip else f"🔔 当前公网 IP：{current_ip}"
            try:
                await bot.send_message(chat_id=CHAT_ID, text=text)
                print(f"✅ IP 通知已发送：{current_ip}")
                last_ip = current_ip
            except Exception as e:
                print(f"❌ 发送失败：{e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_ip = await get_public_ip()
    if current_ip:
        await update.message.reply_text(f"📡 当前公网 IP 是：{current_ip}")
    else:
        await update.message.reply_text("❌ 获取公网 IP 失败。")

# ✅ 改成同步函数
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("ip", ip_command))

    # 注册启动时任务
    async def on_startup(app):
        asyncio.create_task(check_ip_loop(app))
        print("🚀 Bot 启动成功，输入 /ip 可测试")

    app.post_init = on_startup  # 注册启动事件

    # 启动轮询（阻塞式运行）
    app.run_polling()

if __name__ == "__main__":
    main()
