import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import logging
from telegram.error import NetworkError, TimedOut
import time
import threading

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
        "🤖 功能说明：\n" \
        "• 自动监控IP变化（每5分钟检查一次）\n" \
        "• 自动更新Cloudflare DNS记录\n" \
        "• 支持手动触发更新\n\n" \
        "📋 可用命令：\n" \
         "/ip - 获取IP详情并自动检测更新DNS记录\n" \
         "/update - 手动检查并更新DDNS记录\n" \
         "/start - 显示本帮助信息\n\n" \
        "💡 提示：程序会自动监控IP变化，无需手动操作"
    )

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != str(TELEGRAM_CHAT_ID):
        await update.message.reply_text("无权限。请联系管理员绑定chat_id。")
        return
    
    await update.message.reply_text("🔍 正在检查IP信息...")
    
    try:
        public_ip = get_public_ip()
        if not public_ip:
            await update.message.reply_text("❌ 无法获取公网IP")
            return
            
        dns_ip = get_dns_record_ip()
        if not dns_ip:
            await update.message.reply_text("❌ 无法获取DNS记录IP")
            return
        
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
        
        # 构建基础信息
        msg = (
            f"📊 **IP信息详情**\n\n"
            f"🌐 当前公网IP: `{public_ip}`\n"
            f"🔗 DNS记录IP: `{dns_ip}`\n"
            f"🏢 ASN: {asn}\n"
            f"🌍 国家: {country}\n"
            f"🏛️ 所属企业: {org}\n"
            f"📡 ISP类型: {isp_type}\n"
            f"📍 数据来源: ipify.org\n\n"
        )
        
        # 检查IP是否相同并执行相应操作
        if public_ip == dns_ip:
            msg += "✅ **状态**: IP地址一致，无需更新DNS记录"
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            msg += f"⚠️ **检测到IP变化**: {dns_ip} → {public_ip}\n\n🔄 正在自动更新DNS记录..."
            await update.message.reply_text(msg, parse_mode='Markdown')
            
            # 执行DNS更新
            if update_dns_record(public_ip):
                update_msg = f"✅ **DNS更新成功!**\n{CF_RECORD_NAME}: {dns_ip} → {public_ip}"
                # 发送Telegram通知
                send_telegram_message(f"Cloudflare DDNS自动更新成功: {CF_RECORD_NAME} -> {public_ip}")
            else:
                update_msg = f"❌ **DNS更新失败!**\n请检查Cloudflare配置或网络连接"
                # 发送Telegram通知
                send_telegram_message(f"Cloudflare DDNS自动更新失败: {CF_RECORD_NAME}")
            
            await update.message.reply_text(update_msg, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ 检查IP时发生错误: {str(e)}")

async def update_ddns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """手动触发DDNS更新的命令"""
    if str(update.effective_chat.id) != str(TELEGRAM_CHAT_ID):
        await update.message.reply_text("无权限。请联系管理员绑定chat_id。")
        return
    
    await update.message.reply_text("正在检查并更新DDNS记录...")
    
    try:
        public_ip = get_public_ip()
        if not public_ip:
            await update.message.reply_text("❌ 无法获取公网IP")
            return
            
        dns_ip = get_dns_record_ip()
        if not dns_ip:
            await update.message.reply_text("❌ 无法获取DNS记录IP")
            return
            
        if public_ip != dns_ip:
            if update_dns_record(public_ip):
                msg = f"✅ DDNS更新成功!\n{CF_RECORD_NAME}: {dns_ip} → {public_ip}"
            else:
                msg = f"❌ DDNS更新失败!\n当前公网IP: {public_ip}\nDNS记录IP: {dns_ip}"
        else:
            msg = f"ℹ️ IP未发生变化，无需更新\n当前IP: {public_ip}"
            
        await update.message.reply_text(msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 检查DDNS时发生错误: {str(e)}")

def check_and_update_ddns():
    """检查并更新DDNS记录"""
    logger = logging.getLogger(__name__)
    
    try:
        public_ip = get_public_ip()
        if not public_ip:
            logger.error("无法获取公网IP")
            return
            
        dns_ip = get_dns_record_ip()
        if not dns_ip:
            logger.error("无法获取DNS记录IP")
            return
            
        if public_ip != dns_ip:
            logger.info(f"IP发生变化: DNS记录 {dns_ip} -> 公网IP {public_ip}")
            if update_dns_record(public_ip):
                message = f"Cloudflare DDNS更新成功: {CF_RECORD_NAME} -> {public_ip}"
                send_telegram_message(message)
                logger.info(f"DNS记录已更新: {public_ip}")
            else:
                message = f"Cloudflare DDNS更新失败: {CF_RECORD_NAME}"
                send_telegram_message(message)
                logger.error("DNS记录更新失败")
        else:
            logger.debug(f"IP未变化: {public_ip}")
    except Exception as e:
        logger.error(f"DDNS检查过程中发生错误: {e}")

def ddns_check_job():
    """定期检查DDNS的线程任务"""
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            check_and_update_ddns()
            # 每5分钟检查一次
            time.sleep(300)
        except Exception as e:
            logger.error(f"DDNS定期检查任务出错: {e}")
            time.sleep(60)  # 出错后1分钟后重试

def run_bot_with_ddns():
    """同时运行Telegram bot和DDNS检查任务"""
    logger = logging.getLogger(__name__)
    
    try:
        # 启动DDNS检查线程
        ddns_thread = threading.Thread(target=ddns_check_job, daemon=True)
        ddns_thread.start()
        logger.info("DDNS检查线程已启动")
        
        # 创建并运行Telegram bot
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(30).write_timeout(30).connect_timeout(30).pool_timeout(30).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("ip", ip))
        app.add_handler(CommandHandler("update", update_ddns))
        
        # 运行bot（这会自动管理事件循环）
        app.run_polling(drop_pending_updates=True)
            
    except Exception as e:
        logger.error(f"Bot初始化失败: {e}")
        raise

def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 初始DDNS检查
    logger.info("执行初始DDNS检查...")
    check_and_update_ddns()
    
    # 启动Telegram命令Bot
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        max_retries = 5
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                logger.info(f"启动Telegram Bot和DDNS监控... (尝试 {attempt + 1}/{max_retries})")
                
                # 尝试启动bot
                run_bot_with_ddns()
                
                break
                
            except (NetworkError, TimedOut) as e:
                logger.error(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error("达到最大重试次数，程序退出")
                    break
            except Exception as e:
                logger.error(f"未知错误: {e}")
                break

if __name__ == "__main__":
    main()
