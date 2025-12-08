#!/usr/bin/env python3
"""
Keep-alive service for Render to prevent sleep
定时ping服务防止Render休眠
"""

import requests
import time
import threading
import logging
from datetime import datetime
import os
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
PING_INTERVAL = 600  # 10分钟ping一次（Render休眠时间是15分钟）
TARGET_URL = os.environ.get('TARGET_URL', 'http://localhost:8000/health')
DISCORD_WEBHOOK = os.environ.get('DISCORD_WEBHOOK')  # 可选：通知到Discord

def send_discord_notification(message):
    """发送通知到Discord（如果配置了webhook）"""
    if DISCORD_WEBHOOK:
        try:
            requests.post(
                DISCORD_WEBHOOK,
                json={"content": message},
                timeout=10
            )
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

def ping_service():
    """执行ping操作"""
    try:
        response = requests.get(
            TARGET_URL,
            timeout=30,
            headers={
                'User-Agent': 'KeepAlive-Bot/1.0',
                'X-Ping-Source': 'Keep-Alive-Service'
            }
        )

        if response.status_code == 200:
            logger.info(f"✅ Ping successful - Status: {response.json()} {datetime.now()}")
        else:
            logger.warning(f"⚠️ Ping returned status {response.status_code}")

    except requests.exceptions.Timeout:
        logger.error(f"❌ Ping timeout - {datetime.now()}")
        send_discord_notification("🚨 Z-Image service ping timeout!")

    except Exception as e:
        logger.error(f"❌ Ping failed: {str(e)}")
        send_discord_notification(f"🚨 Z-Image service error: {str(e)}")

def schedule_pings():
    """调度定时ping"""
    logger.info(f"🚀 Keep-alive service started, pinging every {PING_INTERVAL} seconds")
    logger.info(f"📍 Target URL: {TARGET_URL}")

    while True:
        # 执行ping
        ping_service()

        # 等待下一次ping
        time.sleep(PING_INTERVAL)

def start_background_ping():
    """在后台启动ping服务"""
    ping_thread = threading.Thread(
        target=schedule_pings,
        daemon=True,  # 设置为守护线程，主程序退出时自动结束
        name="KeepAlive"
    )
    ping_thread.start()
    return ping_thread

@app.route('/keep-alive/status')
def keep_alive_status():
    """返回keep-alive服务状态"""
    return jsonify({
        "status": "running",
        "interval": PING_INTERVAL,
        "target": TARGET_URL,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    # 直接运行时启动ping服务
    print("=" * 50)
    print("Z-Image Keep-Alive Service")
    print(f"Pinging {TARGET_URL} every {PING_INTERVAL} seconds")
    print("=" * 50)

    # 立即执行一次ping
    ping_service()

    # 启动定时ping
    schedule_pings()