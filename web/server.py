#!/usr/bin/env python3
"""
简单的 HTTP 服务器用于前端测试
运行: python server.py
访问: http://localhost:3000
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# 设置端口
PORT = 3000

# 获取当前目录
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 添加 CORS 头部，允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    """启动服务器"""
    try:
        # 切换到 web 目录
        os.chdir(DIRECTORY)

        # 创建服务器
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"🚀 Z-Image 前端测试服务器启动成功!")
            print(f"📱 访问地址: http://localhost:{PORT}")
            print(f"📁 服务目录: {DIRECTORY}")
            print(f"⏹️  按 Ctrl+C 停止服务器")
            print("-" * 50)

            # 自动打开浏览器
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 已自动打开浏览器")
            except:
                print("⚠️  无法自动打开浏览器，请手动访问上述地址")

            # 启动服务器
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用，请尝试其他端口")
        else:
            print(f"❌ 启动失败: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()