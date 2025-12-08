#!/usr/bin/env python3
"""
Render Keep-Alive Service - 作为独立的后台服务运行
这个服务会定期ping主服务以防止休眠
"""

import os
import time
import requests
import logging
from datetime import datetime
from flask import Flask

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 Flask 应用（Render需要）
app = Flask(__name__)

# 配置
MAIN_SERVICE_URL = os.environ.get('MAIN_SERVICE_URL', 'https://z-image-api.onrender.com')
PING_INTERVAL = 600  # 10分钟
PORT = int(os.environ.get('PORT', 8001))

def ping_main_service():
    """Ping主服务"""
    try:
        response = requests.get(
            f"{MAIN_SERVICE_URL}/health",
            timeout=30,
            headers={
                'User-Agent': 'Render-KeepAlive/1.0',
                'X-Ping-Source': 'keepalive-service'
            }
        )

        if response.status_code == 200:
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Keep-alive ping successful")
            return True
        else:
            logger.warning(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Ping returned {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Ping failed: {str(e)}")
        return False

@app.route('/')
def home():
    return {
        "service": "z-image-keepalive",
        "status": "running",
        "main_service": MAIN_SERVICE_URL,
        "ping_interval": PING_INTERVAL
    }

@app.route('/health')
def health():
    return {"status": "healthy"}

def start_keep_alive_loop():
    """在后台启动keep-alive循环"""
    def keep_alive():
        while True:
            ping_main_service()
            time.sleep(PING_INTERVAL)

    import threading
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    logger.info(f"Keep-alive service started - pinging {MAIN_SERVICE_URL} every {PING_INTERVAL} seconds")
    return thread

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Z-Image Keep-Alive Service")
    logger.info(f"Target: {MAIN_SERVICE_URL}")
    logger.info(f"Port: {PORT}")
    logger.info("=" * 50)

    # 立即执行一次ping
    ping_main_service()

    # 启动后台keep-alive
    start_keep_alive_loop()

    # 启动Flask服务（保持服务运行）
    app.run(host='0.0.0.0', port=PORT)