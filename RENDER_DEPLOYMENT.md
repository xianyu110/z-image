# Render 部署指南

## 方法一：使用 Render Blueprint（推荐）

### 1. 准备工作
- 确保代码已推送到 GitHub
- 注册 Render 账号：https://render.com

### 2. 使用 Blueprint 部署

1. 登录 Render 控制台
2. 点击 "New +" → "Blueprint"
3. 连接你的 GitHub 账号
4. 选择 `xianyu110/z-image` 仓库
5. Render 会自动检测 `render.yaml` 文件
6. 点击 "Apply" 开始部署

### 3. 部署后配置
- 后端 API：`https://z-image-api.onrender.com`
- 前端页面：`https://z-image-frontend.onrender.com`

## 方法二：手动创建 Web Service

### 1. 部署后端服务

1. **创建 Web Service**
   - 登录 Render
   - 点击 "New +" → "Web Service"
   - 连接 GitHub 仓库
   - 选择 `z-image` 项目
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python zimage_proxy_simple.py`

2. **配置环境变量**
   ```
   PORT = 8000
   PYTHONUNBUFFERED = true
   ZIMAGE_API_HOST = https://zimage.run
   ```

3. **设置健康检查**
   - Health Check Path: `/health`

### 2. 部署前端服务

1. **创建 Static Site**
   - 点击 "New +" → "Static Site"
   - 连接同一个仓库
   - Root Directory: `web`
   - Build Command: 留空
   - Publish Directory: `.`
   - Add Redirect：
     - Source: `/api/*`
     - Destination: `https://你的后端地址.onrender.com`

### 3. 更新前端配置

部署后，需要更新前端 API 地址：

```javascript
// 在 web/script.js 中修改
const API_CONFIG = {
    baseUrl: 'https://你的后端地址.onrender.com',
    // ...
};
```

## 方法三：单一服务部署（简单）

如果只想部署一个服务：

### 1. 创建新的 Dockerfile

```dockerfile
# Dockerfile.render
FROM node:18-alpine as frontend
WORKDIR /app/web
COPY web/ .
RUN npm install -g http-server

FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask flask-cors requests
COPY . .
RUN mkdir -p /app/web && cp -r web/* /app/web/

EXPOSE $PORT
CMD python -c "from threading import Thread; from zimage_proxy_simple import app; import os; Thread(target=lambda: os.system('cd /app/web && http-server -p 3001 &')).start(); app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))"
```

### 2. 配置服务

- Build Command: `docker build -f Dockerfile.render -t z-image .`
- Start Command: `docker run -p $PORT:8000 z-image`

## 重要配置说明

### 1. 处理 Render 的冷启动

Render 免费版有15分钟不活动会休眠，在 `zimage_proxy_simple.py` 中可以添加：

```python
# 在 app.run() 之前添加
@app.route('/keep-alive')
def keep_alive():
    return {"status": "alive"}
```

### 2. 超时处理

Render 请求超时是30秒，需要优化：

```python
# 在 render.yaml 中添加
envVars:
  - key: RENDER_REQUEST_TIMEOUT
    value: "30000"
```

### 3. CORS 配置

确保后端正确配置 CORS：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["https://你的前端地址.onrender.com"]
    }
})
```

## 部署后验证

1. 检查后端健康状态：
   ```
   curl https://你的后端地址.onrender.com/health
   ```

2. 检查前端访问：
   ```
   打开浏览器访问 https://你的前端地址.onrender.com
   ```

3. 测试图片生成功能

## 常见问题

### 1. 部署失败
- 检查 `requirements.txt` 是否正确
- 确保没有语法错误
- 查看 Render 部署日志

### 2. API 连接失败
- 确认环境变量设置正确
- 检查 CORS 配置
- 查看网络日志

### 3. 冷启动问题
- 使用 ping 服务保持活跃
- 升级到付费计划避免休眠

## 成本优化

1. **免费计划限制**：
   - 750 小时/月
   - 15分钟不活动休眠
   - 带宽限制 100GB

2. **优化建议**：
   - 使用 CDN 减少带宽
   - 优化图片缓存
   - 合理使用 API 调用频率

## 监控和日志

在 Render 控制台可以查看：
- 服务状态
- 访问日志
- 错误日志
- 性能指标

## 域名配置（可选）

1. 在 Render 控制台添加自定义域名
2. 配置 DNS 记录
3. 添加 SSL 证书（自动）