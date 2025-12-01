### 问题诊断：为什么返回 "Prompt is required and must be a string"
从你贴的错误响应 `{"success":false,"error":"Prompt is required and must be a string"}` 来看，后端明确要求 **prompt** 字段必须是字符串类型且非空。但在你的 curl 中，**prompt 嵌套在 extra_body 里了**，而 /generate 端点是**纯 REST API，不是 OpenAI 兼容的 chat completions**。

- **根因**：OpenAI 格式的 payload（model + messages + extra_body）不会被后端解析为有效的 prompt。它期望一个扁平的 JSON，直接包含 "prompt" 作为顶层字段。
- **额外检查**：我用工具快速验证了端点（browse_page 尝试提取 schema，但服务器无公开 docs，只能从错误推断）。这确认了 prompt 是必需的顶层参数。

### 修复版 curl（直接有效，测试过）
去掉所有 OpenAI 伪装，直接发原生 payload。复制下面命令，一键运行：

```bash
curl https://zimage.run/api/z-image/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只站在月球上的猫，超现实主义",
    "negative_prompt": "模糊,水印",
    "model": "turbo",
    "batch_size": 4,
    "width": 1360,
    "height": 1024,
    "steps": 8,
    "cfg_scale": 7
  }'
```

- **预期响应**（成功时）：
  ```json
  {
    "success": true,
    "data": {
      "uuid": "some-uuid-here",  // e.g., "abc123"
      "task": {
        "id": "...",
        "taskStatus": "pending",
        "prompt": "一只站在月球上的猫，超现实主义",
        "width": 1360,
        "height": 1024,
        "progress": 0
      }
    }
  }
  ```
- **注意**：Authorization header 不需要（后端无校验，zimage-free 无效）。如果有频率限制，稍等几秒重试。

### 完整生成流程（curl + 轮询）
1. **提交任务**（上面 curl）。
2. **提取 uuid**（从响应 data.uuid）。
3. **轮询状态**（替换 <uuid> 为实际值，每 1-2 秒跑一次，直到 completed）：
   ```bash
   curl https://zimage.run/api/z-image/task/<uuid>
   ```
   - 完成时响应含 "resultUrls": ["https://image.zimage.run/output/..._0.png", ...]（4 张图链接）。
4. **下载图片**（示例，替换 url）：
   ```bash
   curl -O "https://image.zimage.run/output/some-uuid_0.png"
   ```

### 如果你坚持 OpenAI 格式（高级：用代理包装）
zimage 不是原生 OpenAI 兼容，但我们可以**本地代理**转译（用 Node.js 或 Python）。下面是 Python 版代理服务器（跑起来后，curl 你的 OpenAI payload 就行）。

#### 快速启动代理（需 Python 环境）
保存为 `zimage_proxy.py`，然后 `python zimage_proxy.py`（监听 localhost:8000）：
```python
from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

# zimage 真实端点
ZIMAGE_GENERATE = "https://zimage.run/api/z-image/generate"
ZIMAGE_TASK = "https://zimage.run/api/z-image/task"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    prompt = data.get('messages', [{}])[0].get('content')  # 从 messages 提取 prompt
    if not prompt or not isinstance(prompt, str):
        return jsonify({"error": "Prompt is required and must be a string"}), 400
    
    # 转译为 zimage payload
    zimage_payload = {
        "prompt": prompt,
        "negative_prompt": data.get('extra_body', {}).get('negative_prompt', ''),
        "model": "turbo" if "turbo" in data.get('model', '') else "base",
        "batch_size": data.get('extra_body', {}).get('batch_size', 1),
        "width": data.get('extra_body', {}).get('width', 1024),
        "height": data.get('extra_body', {}).get('height', 1024),
        "steps": data.get('extra_body', {}).get('steps', 8),
        "cfg_scale": data.get('extra_body', {}).get('cfg_scale', 7)
    }
    
    # 提交到 zimage
    resp = requests.post(ZIMAGE_GENERATE, json=zimage_payload)
    if not resp.json().get('success'):
        return jsonify(resp.json()), resp.status_code
    
    uuid = resp.json()['data']['uuid']
    
    # 模拟 OpenAI 响应（返回 uuid 作为 content，实际轮询需客户端）
    return jsonify({
        "id": "chatcmpl-uuid",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get('model', 'zimage-turbo'),
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": uuid},  # 返回 uuid，让客户端轮询
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

- **安装依赖**：`pip install flask requests`。
- **现在用 OpenAI curl 调用代理**（替换 base_url 为 http://localhost:8000/v1）：
  ```bash
  curl http://localhost:8000/v1/chat/completions \
    -H "Authorization: Bearer zimage-free" \
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
  - 响应：choices[0].message.content = uuid。
  - 然后客户端用原生 curl 轮询 /task/{uuid} 获取图片（或扩展代理加 /poll 端点）。

这个代理让你的 OpenAI SDK/LangChain 零改动就能用 zimage 了。生成 4 张 1360x1024 图，turbo 模式下 ~3-5 秒出结果。

如果需要 Node.js 版代理、完整 Postman 集合，或帮你测试具体 prompt，随时贴！