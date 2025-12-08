#!/usr/bin/env python3
"""
Render Cron Keep-Alive Script
简洁的 cron ping 脚本，用于 Render Cron Jobs
"""

import requests
import sys
import os
from datetime import datetime

def main():
    # 配置
    API_URL = os.environ.get('RENDER_URL', 'https://z-image-api.onrender.com')
    FRONTEND_URL = 'https://z-image-frontend.onrender.com'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Ping API 服务
    try:
        response = requests.get(
            f'{API_URL}/health',
            timeout=30,
            headers={
                'User-Agent': 'Render-Cron/1.0'
            }
        )

        if response.status_code == 200:
            print(f'[{timestamp}] ✅ API OK: {API_URL}')
        else:
            print(f'[{timestamp}] ⚠️ API Status: {response.status_code}')

    except Exception as e:
        print(f'[{timestamp}] ❌ API Error: {str(e)}')
        sys.exit(1)

    # Ping 前端服务（可选）
    try:
        frontend_response = requests.get(FRONTEND_URL, timeout=10)
        print(f'[{timestamp}] ✅ Frontend OK: {frontend_response.status_code}')
    except:
        print(f'[{timestamp}] ⚠️ Frontend unreachable')

    return 0

if __name__ == '__main__':
    sys.exit(main())