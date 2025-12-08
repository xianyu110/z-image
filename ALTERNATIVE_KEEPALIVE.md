# Render Keep-Alive 替代方案

由于 Render 的 Cron Jobs 限制，以下是几种有效的 keep-alive 方案：

## 方案一：内置 Keep-Alive（已实现）✅

`zimage_proxy_simple.py` 已经内置了 keep-alive 功能，无需额外配置。

### 工作原理
- 每10分钟自动 ping `/health` 端点
- 使用后台线程，不影响主服务
- 自动启用（通过 `ENABLE_KEEP_ALIVE=true`）

## 方案二：GitHub Actions（推荐）✅

使用 GitHub Actions 定时访问服务。

### 配置文件
`.github/workflows/keep-alive.yml` 已配置好。

### 频率
- 每20分钟自动运行
- 可以在 GitHub Actions 页面查看日志
- 完全免费，不影响 Render 配额

## 方案三：外部监控服务（免费）

### 1. Uptime Robot
```bash
1. 访问 https://uptimerobot.com
2. 注册免费账户
3. 添加 Monitor:
   - Monitor Type: HTTP
   - URL: https://z-image-api.onrender.com/health
   - Monitoring Interval: 5 minutes
```

### 2. Pingdom
```bash
1. 访问 https://www.pingdom.com
2. 免费账户可监控1个网站
3. 设置 URL: https://z-image-api.onrender.com/health
```

### 3. StatusCake
```bash
1. 访问 https://www.statuscake.com
2. 免费计划支持多个监控
3. 配置 URL 和检查间隔
```

## 方案四：第二个 Web Service

创建一个独立的 keep-alive 服务：

### render_keepalive.py
```python
# 已创建，可作为第二个 Web Service 部署
# 需要在 Render 手动创建，不使用 Blueprint
```

### 部署步骤
1. 在 Render 控制台创建新的 Web Service
2. 连接同一个 GitHub 仓库
3. Build Command: `pip install flask requests`
4. Start Command: `python render_keepalive.py`
5. 设置环境变量 `MAIN_SERVICE_URL`

## 方案五：浏览器扩展

创建简单的用户脚本：

```javascript
// Tampermonkey/Greasemonkey 脚本
// ==UserScript==
// @name         Z-Image Keep-Alive
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Keep Z-Image service alive
// @match        https://z-image-api.onrender.com/*
// @grant        none
// ==/UserScript==

setInterval(() => {
    fetch('/health')
        .then(() => console.log('Keep-alive sent'))
        .catch(e => console.error('Keep-alive failed:', e));
}, 300000); // 5分钟
```

## 方案六：桌面应用

简单的 Python 脚���：

```python
# keep_alive_desktop.py
import requests
import time
import tkinter as tk
from datetime import datetime

def ping_service():
    url = "https://z-image-api.onrender.com/health"
    try:
        response = requests.get(url, timeout=30)
        print(f"[{datetime.now()}] ✅ Ping successful")
        return True
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ping failed: {e}")
        return False

def main():
    print("Keep-Alive Desktop Client")
    print("Press Ctrl+C to stop")

    while True:
        ping_service()
        time.sleep(600)  # 10分钟

if __name__ == "__main__":
    main()
```

## 推荐组合

对于最佳效果，使用组合方案：

### 组合1（最简单）
- ✅ 内置 Keep-Alive
- ✅ GitHub Actions

### 组合2（最可靠）
- ✅ 内置 Keep-Alive
- ✅ Uptime Robot
- ✅ GitHub Actions

### 组合3（完全免费）
- ✅ 内置 Keep-Alive
- ✅ GitHub Actions
- ✅ Pingdom（免费版）

## 验证服务状态

### 检查端点
```bash
# API健康检查
curl https://z-image-api.onrender.com/health

# 内置keep-alive状态
curl https://z-image-api.onrender.com/keep-alive/status

# 前端可访问性
curl -I https://z-image-frontend.onrender.com
```

### 查看日志
```bash
# Render 控制台
1. 访问 render.com
2. 选择服务
3. 点击 "Logs"

# GitHub Actions
1. 访问 GitHub 仓库
2. 点击 "Actions"
3. 查看 "Keep Alive Service"

# Uptime Robot
1. 登录后台
2. 查看监控状态
```

## 注意事项

1. **免费限制**
   - Render: 750小时/月
   - GitHub Actions: 2000分钟/月
   - 大多数监控服务有免费配额

2. **最佳实践**
   - 设置合理的ping间隔（5-15分钟）
   - 使用轻量级请求
   - 监控成功率和响应时间

3. **故障排除**
   - 如果服务仍休眠，检查日志
   - 验证请求是否成功
   - 考虑增加监控频率

## 总结

最推荐的方案是**依赖内置 keep-alive + GitHub Actions**。这个组合：
- ✅ 完全免费
- ✅ 无需额外配置
- ✅ 高可靠性
- ✅ 易于监控