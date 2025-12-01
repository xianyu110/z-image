# Z-Image Proxy Server

An OpenAI-compatible proxy server for the Z-Image generation API that allows you to use OpenAI SDKs and libraries with Z-Image's image generation service.

## Features

- **OpenAI-Compatible**: Accepts OpenAI chat completion format requests
- **Automatic Translation**: Converts OpenAI requests to Z-Image API format
- **Task Management**: Handles task submission, status checking, and result polling
- **Error Handling**: Comprehensive error handling and logging
- **Health Monitoring**: Built-in health check endpoint
- **Easy Integration**: Works with existing OpenAI SDKs

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

```bash
python zimage_proxy.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### 1. Generate Images (OpenAI Compatible)
```bash
POST /v1/chat/completions
```

**Request Format:**
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

**Response Format:**
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

#### 2. Check Task Status
```bash
GET /v1/tasks/{uuid}
```

#### 3. Get Completed Images (Polling)
```bash
GET /v1/images/{uuid}
```

#### 4. Health Check
```bash
GET /health
```

### cURL Examples

#### Generate Images:
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

#### Check Task Status:
```bash
curl http://localhost:8000/v1/tasks/{task-uuid}
```

#### Get Final Images:
```bash
curl http://localhost:8000/v1/images/{task-uuid}
```

### Using with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="zimage-free",
    base_url="http://localhost:8000/v1"
)

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
print(f"Task submitted: {task_uuid}")
```

### Testing with the Included Client

The included test client demonstrates how to use the proxy server:

```bash
# Test with default prompt
python test_client.py

# Test with custom prompt
python test_client.py --prompt "A beautiful sunset over mountains" --batch-size 2

# Check server health
python test_client.py --health
```

## Configuration

### Supported Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | Required | Image description |
| `negative_prompt` | string | "" | Things to avoid in image |
| `model` | string | "base" | Model type (base/turbo) |
| `batch_size` | int | 1 | Number of images to generate |
| `width` | int | 1024 | Image width |
| `height` | int | 1024 | Image height |
| `steps` | int | 8 | Number of generation steps |
| `cfg_scale` | int | 7 | CFG scale for guidance |

### Default Settings

- **Server Port**: 8000
- **Model**: turbo (when "turbo" is in model name)
- **Timeout**: 30 seconds for API calls
- **Polling Interval**: 5 seconds
- **Max Polling Attempts**: 60 (5 minutes total)

## Error Handling

The proxy server includes comprehensive error handling:

- **Network Errors**: Handles connection timeouts and failures
- **API Errors**: Propagates Z-Image API errors with proper HTTP status codes
- **Validation Errors**: Validates input parameters before forwarding requests
- **Logging**: Detailed logging for debugging and monitoring

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Server Info
```bash
curl http://localhost:8000/
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the proxy server is running
2. **Timeout Errors**: Check your internet connection and Z-Image service status
3. **Invalid Prompt**: Ensure the prompt is a non-empty string
4. **Batch Size Too Large**: Try smaller batch sizes

### Logs

The server logs detailed information about:
- Request forwarding
- Task submission
- Status polling
- Errors and exceptions

## Architecture

```
Client (OpenAI SDK) → Proxy Server → Z-Image API
                      (Translation)   (Generation)
```

1. Client sends OpenAI-compatible request
2. Proxy server translates to Z-Image format
3. Z-Image API processes the request
4. Proxy server returns OpenAI-compatible response
5. Client polls for results using provided UUID

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues and enhancement requests!