# Z-Image 图片生成代理服务器

一个兼容 OpenAI ���式的 Z-Image 图片生成 API 代理服务器，让你能够使用 OpenAI 的 SDK 和工具库来调用 Z-Image 的图片生成服务。

## ✨ 特性

- **OpenAI 兼容** - 接受标准的 OpenAI chat completion 格式请求
- **自动翻译** - 将 OpenAI 请求自动转换为 Z-Image API 格式
- **任务管理** - 处理任务提交、状态检查和结果轮询
- **错误处理** - 完善的错误处理和日志记录
- **健康监控** - 内置健康检查端点
- **易于集成** - 与现有的 OpenAI SDK 完全兼容
- **多种部署** - 支持本地部署、Vercel 云端部署和 Docker 容器化部署

## 📦 安装

### 方法一：Docker 部署（推荐）

#### 1. 使用 Docker Compose（最简单）

```bash
# 克隆仓库
git clone https://github.com/xianyu110/z-image.git
cd z-image

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 2. 使用 Docker 命令

```bash
# 构建镜像
docker build -t z-image-proxy .

# 运行容器
docker run -d \
  --name z-image-proxy \
  -p 8000:8000 \
  --restart unless-stopped \
  z-image-proxy

# 查看日志
docker logs z-image-proxy

# 停止容器
docker stop z-image-proxy
docker rm z-image-proxy
```

### 方法二：本地部署

1. 克隆或下载这个仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 方法三：Vercel 部署

1. 点击下面的按钮一键部署到 Vercel：

   [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/xianyu110/z-image.git)

2. 或者手动部署（见 [Vercel 部署指南](VERCEL_DEPLOYMENT.md)）

详细部署指南请参考 [Docker 部署指南](DOCKER_DEPLOYMENT.md)。

## 🚀 使用方法

### 本地开发服务器

```bash
python zimage_proxy.py
```

服务器将在 `http://localhost:8001` 启动（端口 8000 可能被占用）

### 云端部署

部署到 Vercel 后，你的 API 端点为：
`https://your-app.vercel.app/api/v1/chat/completions`

### 🔌 API 端点

#### 1. 生成图片（OpenAI 兼容格式）
```bash
POST /api/v1/chat/completions
```

**请求格式：**
```json
{
  "model": "zimage-turbo",
  "messages": [
    {
      "role": "user",
      "content": "一只站在月球上的猫，超现实主义"
    }
  ],
  "extra_body": {
    "prompt": "一只站在月球上的猫，超现实主义",
    "negative_prompt": "模糊,水印",
    "batch_size": 4,
    "width": 1360,
    "height": 1024,
    "steps": 8,
    "cfg_scale": 7
  }
}
```

**响应格式：**
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

#### 2. 检查任务状态
```bash
GET /api/v1/tasks/{uuid}
```

#### 3. 获取完成的图片（自动轮询）
```bash
GET /api/v1/images/{uuid}
```

#### 4. 健康检查
```bash
GET /api/health
```

### 📋 使用示例

#### cURL 命令示例

**本地服务器生成图片：**
```bash
curl http://localhost:8001/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "一只站在月球上的猫，超现实主义"}],
    "extra_body": {
      "prompt": "一只站在月球上的猫，超现实主义",
      "batch_size": 4,
      "width": 1360,
      "height": 1024,
      "negative_prompt": "模糊,水印"
    }
  }'
```

**云端服务器生成图片：**
```bash
curl https://your-app.vercel.app/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "一只站在月球上的猫，超现实主义"}],
    "extra_body": {
      "prompt": "一只站在月球上的猫，超现实主义",
      "batch_size": 4,
      "width": 1360,
      "height": 1024,
      "negative_prompt": "模糊,水印"
    }
  }'
```

**检查任务状态：**
```bash
curl http://localhost:8001/api/v1/tasks/{task-uuid}
```

**获取最终图片：**
```bash
curl http://localhost:8001/api/v1/images/{task-uuid}
```

#### 使用 OpenAI Python SDK

```python
from openai import OpenAI

# 本地服务器
client = OpenAI(
    api_key="zimage-free",  # 可选，仅用于兼容
    base_url="http://localhost:8001/api/v1"
)

# 或者云端服务器
# client = OpenAI(
#     api_key="zimage-free",
#     base_url="https://your-app.vercel.app/api/v1"
# )

response = client.chat.completions.create(
    model="zimage-turbo",
    messages=[
        {"role": "user", "content": "一只站在月球上的猫，超现实主义"}
    ],
    extra_body={
        "prompt": "一只站在月球上的猫，超现实主义",
        "negative_prompt": "模糊,水印",
        "batch_size": 4,
        "width": 1360,
        "height": 1024
    }
)

task_uuid = response.choices[0].message.content
print(f"任务已提交，UUID: {task_uuid}")
```

#### 使用内置测试客户端

内置的测试客户端演示了如何使用代理服务器：

```bash
# 使用默认提示词测试
python3 test_client.py

# 使用自定义提示词测试
python3 test_client.py --prompt "美丽的日落山景" --batch-size 2

# 检查服务器健康状态
python3 test_client.py --health

# 指定服务器地址
python3 test_client.py --base-url http://localhost:8001
```

## ⚙️ 配置说明

### 支持的参数

| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `prompt` | string | 必需 | 图片描述文字 |
| `negative_prompt` | string | "" | 要避免的内容描述 |
| `model` | string | "base" | 模型类型 (base/turbo) |
| `batch_size` | int | 1 | 生成图片数量 |
| `width` | int | 1024 | 图片宽度 |
| `height` | int | 1024 | 图片高度 |
| `steps` | int | 8 | 生成步数 |
| `cfg_scale` | int | 7 | 引导强度 |

### 默认设置

- **服务器端口**: 8001（本地）
- **默认模型**: turbo（当模型名称包含"turbo"时）
- **超时时间**: API 调用 30 秒
- **轮询间隔**: 5 秒
- **最大轮询次数**: 60 次（总计 5 分钟）

## 🛡️ 错误处理

代理服务器包含完善的错误处理机制：

- **网络错误**: 处理连接超时和失败
- **API 错误**: 传播 Z-Image API 错误并附带正确的 HTTP 状态码
- **验证错误**: 在转发请求前验证输入参数
- **日志记录**: 详细的日志记录用于调试和监控

## 📊 监控

### 健康检查
```bash
# 本地服务器
curl http://localhost:8001/api/health

# 云端服务器
curl https://your-app.vercel.app/api/health
```

### 服务器信息
```bash
# 本地服务器
curl http://localhost:8001/api/

# 云端服务器
curl https://your-app.vercel.app/api/
```

## 🔧 故障排除

### 常见问题

1. **连接被拒绝**: 确保代理服务器正在运行
2. **超时错误**: 检查你的网络连接和 Z-Image 服务状态
3. **无效提示词**: 确保提示词是非空字符串
4. **批量大小过大**: 尝试使用较小的批量大小
5. **端口占用**: 如果 8000 端口被占用，服务器会自动使用 8001 端口

### 日志信息

服务器会记录详细的信息：
- 请求转发
- 任务提交
- 状态轮询
- 错误和异常

## 🏗️ 架构说明

```
客户端 (OpenAI SDK) → 代理服务器 → Z-Image API
                     (格式转换)    (图片生成)
```

1. 客户端发送 OpenAI 兼容的请求
2. 代理服务器将其翻译为 Z-Image 格式
3. Z-Image API 处理请求
4. 代理服务器返回 OpenAI 兼容的响应
5. 客户端使用提供的 UUID 轮询获取结果

## 📄 许可证

本项目仅供教育和开发目的使用。

## 🤝 贡献

欢迎提交问题反馈和功能请求！

## 🌟 支持

如果这个项目对你有帮助，请给个 ⭐ Star！

### 相关链接

- [Z-Image 官方网站](https://zimage.run/)
- [Vercel 部署指南](VERCEL_DEPLOYMENT.md)
- [问题反馈](https://github.com/xianyu110/z-image/issues)

### 技术栈

- **后端**: Python (Flask / Vercel Serverless)
- **部���**: Vercel (Serverless Functions)
- **API**: OpenAI Compatible / Z-Image API
- **无外部依赖**: 仅使用 Python 标准库