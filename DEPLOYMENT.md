# 部署指南

本指南说明如何将 Z-Image 代理服务器部署到不同的云平台。

## 🚀 Vercel 部署（Serverless）

Vercel 是一个无服务器平台，自动处理扩展和基础设施。

### 方法一：一键部署（推荐）

1. 点击下面的按钮：

   [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/xianyu110/z-image.git)

2. 授权 Vercel 访问你的 GitHub 账户
3. 输入项目名称（可选）
4. 点击 "Deploy" 按钮
5. 等待部署完成（通常需要 1-2 分钟）

### 方法二：手动部署

1. **安装 Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **登录 Vercel**
   ```bash
   vercel login
   ```

3. **克隆项目**
   ```bash
   git clone https://github.com/xianyu110/z-image.git
   cd z-image
   ```

4. **部署项目**
   ```bash
   vercel --prod
   ```

### Vercel 配置说明

项目已包含 `vercel.json` 配置文件：

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/z-image.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/v1/chat/completions",
      "dest": "/api/z-image.py"
    },
    {
      "src": "/api/v1/tasks/(.*)",
      "dest": "/api/z-image.py"
    },
    {
      "src": "/api/v1/images/(.*)",
      "dest": "/api/z-image.py"
    },
    {
      "src": "/api/health",
      "dest": "/api/z-image.py"
    },
    {
      "src": "/api/",
      "dest": "/api/z-image.py"
    }
  ]
}
```

### 部署后的 URL

部署成功后，你的 API 端点为：
- 主 API：`https://your-app.vercel.app/api/v1/chat/completions`
- 健康检查：`https://your-app.vercel.app/api/health`

## 🎨 Render 部署（容器化）

Render 提供了简单易用的容器部署服务，支持免费套餐。

### 方法一：通过 GitHub 连接（推荐）

1. **登录 Render Dashboard**
   - 访问 [render.com](https://render.com)
   - 使用 GitHub 账户登录

2. **创建新的 Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的 GitHub 账户
   - 选择 `z-image` 仓库

3. **配置服务**
   - **Name**: `z-image-proxy`（或你喜欢的名称）
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: `Free`（或根据需要选择）

4. **设置环境变量**
   - 不需要额外的环境变量，但可以设置：
   - `PORT`: `8000`（Render 自动设置）
   - `PYTHON_VERSION`: `3.9.0`

5. **创建服务**
   - 点击 "Create Web Service"
   - 等待部署完成（通常需要 2-3 分钟）

### 方法二：使用 render.yaml 配置

1. **确保项目根目录有 render.yaml**
   ```yaml
   services:
     - type: web
       name: z-image-proxy
       runtime: python
       plan: free
       buildCommand: "pip install -r requirements.txt"
       startCommand: "python app.py"
       envVars:
         - key: PORT
           value: 8000
   ```

2. **通过 GitHub 部署**
   - 推送代码到 GitHub
   - 在 Render 中导入仓库
   - Render 会自动识别 `render.yaml` 配置

### Render 配置说明

- **主应用文件**: `app.py`（Flask 服务器）
- **依赖文件**: `requirements.txt`
- **端口**: Render 通过 `PORT` 环境变量自动设置
- **健康检查**: Render 会自动访问 `/` 端点检查服务状态

### 部署后的 URL

部署成功后，你的 API 端点为：
- 主 API：`https://your-app.onrender.com/api/v1/chat/completions`
- 健康检查：`https://your-app.onrender.com/api/health`

## 🐳 Docker 部署

如果你更喜欢 Docker 容器化部署：

### 1. 使用 Docker Compose

```bash
# 克隆项目
git clone https://github.com/xianyu110/z-image.git
cd z-image

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 2. 使用简化版 Docker（解决 APT 问题）

```bash
# 使用 Alpine Linux 版本
docker-compose -f docker-compose.simple.yml up -d
```

### 3. 使用 Docker Hub 镜像

```bash
# 拉取镜像
docker pull xianyu110/z-image:latest

# 运行容器
docker run -d \
  --name z-image-proxy \
  -p 8000:8000 \
  xianyu110/z-image:latest
```

## 📋 平台对比

| 特性 | Vercel | Render | Docker |
|------|--------|--------|--------|
| 部署难度 | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 冷启动 | 有 | 无 | 无 |
| 免费额度 | 100GB/月 | 750小时/月 | 取决于服务器 |
| 自定义域名 | 支持 | 支持 | 需要配置 |
| SSL 证书 | 自动 | 自动 | 需要配置 |
| 扩展性 | 自动 | 手动 | 手动 |

## 🔧 环境变量配置

### Vercel

在 Vercel Dashboard 中设置环境变量：
1. 进入项目设置
2. 点击 "Environment Variables"
3. 添加所需变量

### Render

在 Render Dashboard 中设置环境变量：
1. 进入服务设置
2. 点击 "Environment"
3. 添加所需变量

### 通用环境变量

本项目不需要特殊的环境变量，但你可以设置：

```bash
# 服务器端口（Render 自动设置）
PORT=8000

# Python 版本
PYTHON_VERSION=3.9.0

# 时区（可选）
TZ=Asia/Shanghai
```

## 🛠️ 故障排除

### Vercel 常见问题

1. **函数超时**
   - Vercel 函数最大执行时间为 10 秒
   - 图片生成可能需要更长时间，建议使用任务轮询方式

2. **冷启动延迟**
   - 首次请求可能需要 2-3 秒
   - 后续请求会更快

3. **依赖安装失败**
   - 检查 `vercel.json` 中的 Python 版本
   - 确保 `requirements.txt` 格式正确

### Render 常见问题

1. **构建失败**
   - 检查 `requirements.txt` 版本兼容性
   - 查看构建日志定位问题

2. **服务不响应**
   - 检查 Start Command 是否正确
   - 确保 `app.py` 监听正确的端口

3. **内存不足**
   - 免费套餐内存有限
   - 考虑升级到付费套餐

### 通用问题

1. **API 调用失败**
   ```bash
   # 检查健康状态
   curl https://your-domain/api/health
   ```

2. **CORS 错误**
   - 本地测试时使用代理
   - 部署后通常不会有此问题

3. **性能优化**
   - 使用 CDN 加速图片访问
   - 实现结果缓存
   - 批量请求合并

## 📚 使用示例

部署成功后，你可以使用以下方式调用 API：

### 使用 curl

```bash
curl https://your-domain/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "一只可爱的猫咪"}],
    "extra_body": {
      "batch_size": 4,
      "width": 1024,
      "height": 1024
    }
  }'
```

### 使用 OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="zimage-free",
    base_url="https://your-domain/api/v1"
)

response = client.chat.completions.create(
    model="zimage-turbo",
    messages=[
        {"role": "user", "content": "一只可爱的猫咪"}
    ],
    extra_body={
        "batch_size": 4,
        "width": 1024,
        "height": 1024
    }
)

print(response.choices[0].message.content)
```

## 🆕 获取帮助

如果遇到问题：

1. 查看 [GitHub Issues](https://github.com/xianyu110/z-image/issues)
2. 阅读 [官方文档](https://zimage.run/)
3. 提交新的 Issue 或 Pull Request

## 🌟 下一步

部署成功后，你可以：

- 集成到你的应用中
- 开发自定义客户端
- 添加额外功能（如图像处理、缓存等）
- 监控 API 使用情况