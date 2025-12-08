# Keep-Alive（防休眠）配置指南

## 概述

Render 免费计划在 15 分钟无活动后会休眠服务。本指南提供了多种防止服务休眠的解决方案。

## 方案一：内置 Keep-Alive（推荐）

### 自动启用
`zimage_proxy_simple.py` 已内置 keep-alive 功能，默认启用。

### 配置
```bash
# 启用 keep-alive（默认）
export ENABLE_KEEP_ALIVE=true

# 禁用 keep-alive
export ENABLE_KEEP_ALIVE=false

# 设置 ping 间隔（可选，默认 10 分钟）
export KEEP_ALIVE_INTERVAL=600
```

### 工作原理
- 每 10 分钟自动访问 `/health` 端点
- 使用后台线程运行，不影响主服务
- 日志显示 "Keep-alive ping sent"

## 方案二：GitHub Actions 定时任务

### 自动执行
文件位置：`.github/workflows/keep-alive.yml`

### 功能
- 每 20 分钟自动运行
- 同时 ping API 和前端服务
- 支持 JSON 响应解析
- 提供详细的日志输出

### 查看日志
1. 访问 GitHub 仓库
2. 点击 "Actions" 标签
3. 查看 "Keep Alive Service" 工作流

## 方案三：Render Cron Jobs

### 配置
`render.yaml` 已包含 cron 服务配置。

### 特点
- 每 10 分钟运行一次
- 自动部署
- 独立的服务进程
- 在 Render 控制台查看日志

## 方案四：外部服务

### PythonAnywhere
```python
# 在 PythonAnywhere 设置定时任务
import requests
url = "https://z-image-api.onrender.com/health"
requests.get(url)
```

### Uptime Robot（免费）
1. 注册 https://uptimerobot.com
2. 添加监控：`https://z-image-api.onrender.com/health`
3. 设置间隔：5 分钟

### 其他服务
- [StatusCake](https://www.statuscake.com)
- [Pingdom](https://www.pingdom.com)
- [Better Uptime](https://betteruptime.com)

## 方案五：客户端 Keep-Alive

### JavaScript（前端）
```javascript
// 每 10 分钟 ping 后端
setInterval(async () => {
    try {
        await fetch('/api/health');
        console.log('Keep-alive sent');
    } catch (e) {
        console.error('Keep-alive failed:', e);
    }
}, 600000); // 10分钟
```

### Python 脚本
```bash
# 运行外部 ping 脚本
python3 external_cron.py
```

## 监控和日志

### 检查服务状态
```bash
# 快速健康检查
python3 check_health.py

# 查看服务日志
docker logs -f z-image-proxy

# 查看特定端点
curl https://z-image-api.onrender.com/keep-alive/status
```

### 日志示例
```
[2024-01-01 12:00:00] Starting Z-Image Simple Proxy Server
[2024-01-01 12:00:00] Keep-alive service started (pinging every 10 minutes)
[2024-01-01 12:10:00] Keep-alive ping sent
[2024-01-01 12:20:00] Keep-alive ping sent
```

## 故障排除

### 服务仍然休眠
1. 检查 cron 日志：`grep "keep-alive" render.log`
2. 验证健康端点：`curl /health`
3. 检查时间间隔是否正确

### Keep-alive 失败
1. 网络问题：增加 timeout
2. 服务重启：检查 restart 策略
3. 资源限制：查看 Render 控制台

### 最佳实践
1. 使用多种方案（冗余）
2. 监控 ping 成功率
3. 设置告警通知
4. 定期检查服务状态

## 成本考虑

### 免费限制
- Render：750 小时/月
- GitHub Actions：2000 分钟/月
- Uptime Robot：50 个监控

### 优化建议
- 合理设置 ping 间隔（10-15 分钟）
- 使用轻量级健康检查
- 避免不必要的请求

## 高级配置

### Discord 通知
```bash
# 设置 Discord Webhook
export DISCORD_WEBHOOK="你的webhook地址"
```

### 自定义 Ping 路径
```javascript
// 在 zimage_proxy_simple.py 中添加
@app.route('/custom-ping')
def custom_ping():
    return {"status": "custom-pong", "timestamp": datetime.now()}
```

### 动态间隔
```python
# 根据使用情况调整 ping 间隔
if recent_activity:
    interval = 300  # 5分钟
else:
    interval = 900  # 15分钟
```

## 总结

推荐使用方案组合：
1. **内置 Keep-Alive**：主要防护
2. **GitHub Actions**：备份方案
3. **Uptime Robot**：额外监控

这样即使某个方案失败，其他方案仍能保持服务活跃。