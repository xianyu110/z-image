#!/usr/bin/env python3
"""
外部cron服务，用于定时ping Render 服务
可以部署在任何在线服务上（如 GitHub Actions, Vercel, PythonAnywhere 等）
"""

import requests
import time
import os
from datetime import datetime
import json
import schedule

# 配置要ping的服务列表
SERVICES_TO_PING = [
    os.environ.get('RENDER_URL', 'https://z-image-api.onrender.com'),
    # 可以添加更多URL
    # 'https://your-backend-2.onrender.com',
]

# ping间隔（分钟）
PING_INTERVAL = 10

# 日志文件
LOG_FILE = 'ping_log.txt'

def log_message(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry, end="")

    # 可选：写入日志文件
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except:
        pass

def ping_service(url):
    """ping单个服务"""
    try:
        # ping健康检查端点
        response = requests.get(
            f"{url}/health",
            timeout=30,
            headers={
                'User-Agent': 'Keep-Alive-Cron/1.0',
                'X-Cron-Source': 'External-Service'
            }
        )

        if response.status_code == 200:
            log_message(f"✅ {url} - OK ({response.elapsed.total_seconds():.2f}s)")
            return True
        else:
            log_message(f"⚠️ {url} - Status: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        log_message(f"❌ {url} - Timeout")
        return False
    except Exception as e:
        log_message(f"❌ {url} - Error: {str(e)}")
        return False

def ping_all_services():
    """ping所有服务"""
    log_message(f"\n{'='*50}")
    log_message("Starting ping cycle...")

    success_count = 0
    for service in SERVICES_TO_PING:
        if service:  # 确保URL不为空
            if ping_service(service):
                success_count += 1
            time.sleep(2)  # 避免同时请求

    log_message(f"Ping cycle complete: {success_count}/{len(SERVICES_TO_PING)} services online")

def main():
    """主函数"""
    log_message("\n🚀 Keep-Alive Cron Service Started")
    log_message(f"Pinging {len(SERVICES_TO_PING)} services every {PING_INTERVAL} minutes")
    log_message(f"Services: {SERVICES_TO_PING}")

    # 立即执行一次
    ping_all_services()

    # 设置定时任务
    schedule.every(PING_INTERVAL).minutes.do(ping_all_services)

    # 运行循环
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    main()