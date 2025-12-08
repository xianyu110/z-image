#!/usr/bin/env python3
"""
快速检查所有服务的健康状态
"""

import requests
import json
from datetime import datetime
import sys

# 服务列表
SERVICES = {
    "Backend API": "http://localhost:8000/health",
    "Frontend": "http://localhost:3000",
    "Render API": "https://z-image-api.onrender.com/health",
    "Render Frontend": "https://z-image-frontend.onrender.com"
}

def check_service(name, url):
    """检查单个服务"""
    try:
        if url == "http://localhost:3000":
            # 前端是静态服务，只检查是否能访问
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True, "OK"
            return False, f"HTTP {response.status_code}"
        else:
            # API服务检查健康端点
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, data.get('status', 'OK')
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("\n" + "="*60)
    print(f"Z-Image Service Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    all_ok = True

    for name, url in SERVICES.items():
        is_ok, status = check_service(name, url)
        icon = "✅" if is_ok else "❌"
        print(f"{icon} {name:20} {url:40} [{status}]")
        if not is_ok:
            all_ok = False

    print("="*60)

    if all_ok:
        print("✅ All services are healthy!")
        sys.exit(0)
    else:
        print("❌ Some services are down!")
        sys.exit(1)

if __name__ == "__main__":
    main()