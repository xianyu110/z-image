# Vercel 部署指南

Z-Image代理服务器的Vercel无服务器部署版本。

## 📁 项目结构

```
z-image/
├── api/
│   └── z-image.py           # 主要的无服务器函数
├── vercel.json              # Vercel配置文件
├── package.json             # Node.js项目配置
├── vercel_requirements.txt  # Python依赖（空 - 仅使用标准库）
└── README.md                # 项目文档
```

## 🚀 部署步骤

### 1. 安装Vercel CLI

```bash
npm i -g vercel
```

### 2. 登录Vercel

```bash
vercel login
```

### 3. 部署到Vercel

在项目根目录运行：

```bash
vercel
```

或者直接部署到生产环境：

```bash
vercel --prod
```

## 🔧 配置说明

### Vercel配置 (vercel.json)

- **运行时**: Python 3.9
- **路由规则**: 将API请求转发到无服务器函数
- **构建配置**: 使用@vercel/python构建器

### 支持的端点

部署后的API端点格式为：
- `https://your-domain.vercel.app/api/v1/chat/completions`
- `https://your-domain.vercel.app/api/v1/tasks/{uuid}`
- `https://your-domain.vercel.app/api/v1/images/{uuid}`
- `https://your-domain.vercel.app/api/health`
- `https://your-domain.vercel.app/api/`

## 🧪 本地测试

### 1. 安装依赖

```bash
npm install
```

### 2. 本地开发

```bash
vercel dev
```

这将启动本地开发服务器，通常在 `http://localhost:3000`

### 3. 测试API

```bash
# 测试健康检查
curl http://localhost:3000/api/health

# 测试图片生成
curl http://localhost:3000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "一只站在月球上的猫"}],
    "extra_body": {
      "batch_size": 1,
      "width": 1024,
      "height": 1024
    }
  }'
```

## 🌐 生产环境使用

### cURL示例

```bash
# 生成图片
curl https://your-app.vercel.app/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zimage-turbo",
    "messages": [{"role": "user", "content": "A beautiful sunset over mountains"}],
    "extra_body": {
      "batch_size": 4,
      "width": 1360,
      "height": 1024,
      "negative_prompt": "blurry,watermark"
    }
  }'

# 检查任务状态
curl https://your-app.vercel.app/api/v1/tasks/{task-uuid}

# 获取最终图片
curl https://your-app.vercel.app/api/v1/images/{task-uuid}
```

### JavaScript/Node.js示例

```javascript
// 使用fetch API
async function generateImage(prompt) {
  const response = await fetch('https://your-app.vercel.app/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'zimage-turbo',
      messages: [
        { role: 'user', content: prompt }
      ],
      extra_body: {
        batch_size: 1,
        width: 1024,
        height: 1024
      }
    })
  });

  const result = await response.json();
  return result;
}

// 使用示例
generateImage('A cat on the moon, surrealism')
  .then(result => console.log(result))
  .catch(error => console.error(error));
```

### Python示例

```python
import requests
import time

def generate_image(prompt):
    url = "https://your-app.vercel.app/api/v1/chat/completions"

    response = requests.post(url, json={
        "model": "zimage-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "extra_body": {
            "batch_size": 1,
            "width": 1024,
            "height": 1024
        }
    })

    return response.json()

# 使用示例
result = generate_image("A cat on the moon, surrealism")
task_uuid = result['choices'][0]['message']['content']
print(f"Task UUID: {task_uuid}")
```

## ⚙️ 环境变量

如需配置环境变量，在Vercel控制台中设置：

```bash
# 设置环境变量
vercel env add VARIABLE_NAME
```

当前版本不需要额外的环境变量，但未来可以添加：
- `ZIMAGE_API_HOST` - 自定义Z-Image API主机
- `LOG_LEVEL` - 日志级别
- `TIMEOUT` - 请求超时时间

## 📊 监控和日志

- Vercel提供了内置的日志查看功能
- 在Vercel控制台查看函数执行日志
- 可以设置监控和警报

## 🔒 安全注意事项

- API是公开的，任何人都可以访问
- Z-Image API目前不需要认证
- 可以在Vercel中设置速率限制
- 建议监控API使用情况

## 🚀 性能优化

- Vercel自动处理函数冷启动
- 使用CDN缓存静态响应
- 函数有执行时间限制（默认10秒）
- 图片生成可能需要多次轮询

## 🔧 故障排除

### 常见问题

1. **函数超时**
   - 增加vercel.json中的超时设置
   - 优化轮询逻辑

2. **CORS错误**
   - 在响应中添加CORS头
   - 使用代理服务器

3. **内存不足**
   - 减少并发请求
   - 优化内存使用

### 调试

```bash
# 查看函数日志
vercel logs

# 本地调试
vercel dev --debug
```

## 📝 更新部署

当需要更新代码时：

1. 修改代码
2. 提交到git
3. 运行 `vercel --prod`

Vercel会自动重新部署。

## 💡 扩展功能

可以添加的功能：
- 用户认证
- 使用统计
- 图片缓存
- 批量处理
- 自定义模型参数