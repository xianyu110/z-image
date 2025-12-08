#!/bin/bash

# 启动Z-Image服务并启用Keep-Alive

echo "==================================="
echo "Z-Image Service with Keep-Alive"
echo "==================================="

# 设置环境变量
export ENABLE_KEEP_ALIVE=true
export PORT=${PORT:-8000}

# 启动主服务
echo "Starting main service on port $PORT..."
python3 zimage_proxy_simple.py

# 如果主服务退出，保持容器运行的备用方案
echo "Main service stopped, starting keep-alive only..."
python3 -c "
import requests
import time
import os
from datetime import datetime

url = f'http://localhost:{os.environ.get(\"PORT\", 8000)}/health'
print(f'Keep-alive service monitoring: {url}')

while True:
    try:
        time.sleep(600)  # 10分钟
        requests.get(url, timeout=5)
        print(f'[{datetime.now()}] Keep-alive ping sent')
    except Exception as e:
        print(f'Keep-alive error: {e}')
"