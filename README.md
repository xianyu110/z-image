# Z-Image 图片生成代理服务器

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/xianyu110/z-image.git)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/xianyu110/z-image.git)

一个兼容 OpenAI 格式的 Z-Image 图片生成 API 代理服务器，让你能够使用 OpenAI 的 SDK 和工具库来调用 Z-Image 的图片生成服务。

## ✨ 特性

- 🔄 **OpenAI 兼容** - 完全兼容 OpenAI Chat Completions API 格式
- 🔀 **智能转换** - 自动将 OpenAI 请求转换为 Z-Image API 格式
- 📋 **任务管理** - 支持异步任务提交、状态检查和结果轮询
- 🛡️ **错误处理** - 完善的错误处理机制和详细的日志记录
- 💚 **健康监控** - 内置健康检查端点，便于监控服务状态
- 🔌 **易于集成** - 与现有 OpenAI SDK 无缝集成，无需修改代码
- 🎨 **Web 界面** - 提供现代化的 Web 测试界面
- ☁️ **多云部署** - 支持 Vercel、Render、Docker 等多种部署方式
- ⚡ **零依赖** - 核心功能仅使用 Python 标准库，部署更轻量

## 🚀 快速开始

### 一键部署到云端

#### Vercel (Serverless)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/xianyu110/z-image.git)

#### Render (容器化)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/xianyu110/z-image.git)

### 本地部署

#### 1. 使用 Docker (推荐)

```bash
# 克隆项目
git clone https://github.com/xianyu110/z-image.git
cd z-image

# 启动服务
docker-compose up -d

# 访问 API
curl http://localhost:8000/api/health
```

#### 2. 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python zimage_proxy.py

# 或使用 Flask 服务器（适用于 Render 部署）
python app.py
```

服务器将在 `http://localhost:8001` 启动

## 📖 API 使用

### 基础端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat/completions` | POST | 生成图片（OpenAI 兼容） |
| `/api/v1/tasks/{uuid}` | GET | 查询任务状态 |
| `/api/v1/images/{uuid}` | GET | 获取生成结果 |
| `/api/health` | GET | 健康检查 |

### 生成图片示例

#### 使用 cURL

```bash
# 本地服务器
curl http://localhost:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "一只可爱的猫咪，卡通风格"}],
    "extra_body": {
      "batch_size": 4,
      "width": 1024,
      "height": 1024,
      "steps": 8,
      "cfg_scale": 7
    }
  }'

# Vercel 部署
curl https://your-app.vercel.app/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{...}'

# Render 部署
curl https://your-app.onrender.com/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{...}'
```

#### 使用 OpenAI Python SDK

```python
from openai import OpenAI

# 配置客户端
client = OpenAI(
    api_key="zimage-free",  # 可选，仅用于兼容
    base_url="http://localhost:8001/api/v1"  # 或你的云端地址
)

# 生成图片
response = client.chat.completions.create(
    model="zimage-turbo",
    messages=[
        {"role": "user", "content": "一只可爱的猫咪，卡通风格"}
    ],
    extra_body={
        "batch_size": 4,
        "width": 1024,
        "height": 1024,
        "negative_prompt": "模糊，低质量",
        "steps": 8,
        "cfg_scale": 7
    }
)

# 获取任务 UUID
task_uuid = response.choices[0].message.content
print(f"任务 UUID: {task_uuid}")

# 获取生成结果（使用额外的端点）
import requests
result = requests.get(f"http://localhost:8001/api/v1/images/{task_uuid}")
print(result.json())
```

#### 使用 Node.js

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'zimage-free', // 可选
  baseURL: 'http://localhost:8001/api/v1'
});

async function generateImage() {
  const response = await client.chat.completions.create({
    model: 'zimage-turbo',
    messages: [
      { role: 'user', content: '一只可爱的猫咪，卡通风格' }
    ],
    extra_body: {
      batch_size: 4,
      width: 1024,
      height: 1024
    }
  });

  const taskUuid = response.choices[0].message.content;
  console.log('Task UUID:', taskUuid);
}
```

## 🎨 Web 测试界面

项目提供了一个现代化的 Web 测试界面：

```bash
# 启动 Web 界面
cd web
python server.py

# 访问 http://localhost:3000
```

### 功能特性

- 🎯 直观的图片生成界面
- ⚙️ 实时参数调整
- 📊 生成进度监控
- 🖼️ 图片预览和下载
- 📱 响应式设计

## ⚙️ 参数说明

### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `prompt` | string | ✅ | - | 图片描述文字 |
| `negative_prompt` | string | ❌ | "" | 负面提示词 |
| `model` | string | ❌ | "zimage-turbo" | 模型名称 |
| `batch_size` | int | ❌ | 1 | 生成图片数量 (1-4) |
| `width` | int | ❌ | 1024 | 图片宽度 |
| `height` | int | ❌ | 1024 | 图片高度 |
| `steps` | int | ❌ | 8 | 生成步数 |
| `cfg_scale` | int | ❌ | 7 | 引导强度 |

### 响应格式

```json
{
  "id": "chatcmpl-uuid",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "zimage-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "task-uuid-here",
        "task_uuid": "task-uuid-here"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

## 🏗️ 部署指南

### Vercel 部署

1. **一键部署**：点击顶部的 "Deploy with Vercel" 按钮
2. **手动部署**：
   ```bash
   npm i -g vercel
   vercel --prod
   ```

**优点**：
- 无服务器，自动扩展
- 免费 100GB 带宽/月
- 全球 CDN 加速
- 自动 HTTPS

**注意**：
- 函数执行时间限制 10 秒
- 冷启动延迟 2-3 秒

### Render 部署

1. 访问 [render.com](https://render.com)
2. 用 GitHub 账户登录
3. 创建新的 Web Service
4. 配置：
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

**优点**：
- 常驻服务，无冷启动
- 免费 750 小时/月
- 支持后台任务
- 自动部署

### Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用简化版本
docker-compose -f docker-compose.simple.yml up -d

# 使用 Makefile
make quickstart
```

## 🔧 高级配置

### 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `PORT` | 8000 | 服务器端口 |
| `PYTHON_VERSION` | 3.9 | Python 版本 |
| `TZ` | UTC | 时区设置 |

### 监控和日志

```bash
# 检查服务状态
curl http://localhost:8001/api/health

# 查看实时日志（Docker）
docker-compose logs -f

# 查看服务信息
curl http://localhost:8001/api/
```

## 🛠️ 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 错误：Port 8000 is already in use
   # 解决：服务器会自动切换到 8001 端口
   ```

2. **超时错误**
   ```bash
   # 检查网络连接
   ping zimage.run

   # 增加超时时间
   export TIMEOUT=60
   ```

3. **批量生成失败**
   ```bash
   # 减少批量大小
   "batch_size": 1
   ```

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python zimage_proxy.py
```

## 📊 性能优化

- **批量请求**：使用 `batch_size` 一次生成多张图片
- **缓存结果**：保存生成的图片 URL，避免重复请求
- **异步处理**：使用任务队列处理大量请求

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 📄 许可证

本项目仅供教育和学习目的使用。

## 🌟 致谢

- [Z-Image](https://zimage.run/) - 图片生成服务
- [OpenAI](https://openai.com/) - API 规范参考

## 📞 支持

- 🐛 [报告问题](https://github.com/xianyu110/z-image/issues)
- 💬 [讨论区](https://github.com/xianyu110/z-image/discussions)
- 📧 邮箱：[your-email@example.com]

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！