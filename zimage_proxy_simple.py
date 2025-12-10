from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging
from datetime import datetime
import threading
import os

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Z-Image API endpoints
ZIMAGE_GENERATE = "https://zimage.run/api/z-image/generate"
ZIMAGE_TASK = "https://zimage.run/api/z-image/task"

# 任务缓存
task_cache = {}

# Keep-alive 功能
def start_keep_alive():
    """启动keep-alive后台线程"""
    if os.environ.get('ENABLE_KEEP_ALIVE', 'true').lower() == 'true':
        try:
            # 定义keep-alive函数
            def keep_alive():
                while True:
                    try:
                        # 每10分钟ping一次（Render休眠时间是15分钟）
                        time.sleep(600)
                        # 访问健康检查端点保持活跃
                        requests.get(f"http://localhost:{os.environ.get('PORT', 8000)}/health", timeout=5)
                        logger.info("Keep-alive ping sent")
                    except Exception as e:
                        logger.warning(f"Keep-alive ping failed: {e}")

            # 启动后台线程
            keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
            keep_alive_thread.start()
            logger.info("Keep-alive service started (pinging every 10 minutes)")
        except RuntimeError as e:
            if "can't start new thread" in str(e):
                logger.warning("Thread limit reached, disabling keep-alive service")
                logger.info("Server will continue running without keep-alive service")
            else:
                raise e
        except Exception as e:
            logger.error(f"Failed to start keep-alive service: {e}")

@app.route('/')
def home():
    return jsonify({
        "service": "zimage-proxy-simple",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "completions": "/v1/chat/completions",
            "task": "/v1/tasks/<taskId>",
            "image": "/v1/images/<taskId>"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/v1/chat/completions', methods=['POST', 'OPTIONS'])
def chat_completions():
    """简化的图片生成接口"""
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        prompt = messages[0].get('content')
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # 构建简化的请求
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512,
            "steps": 4,
            "batch_size": 1,
            "cfg_scale": 6
        }

        logger.info(f"Submitting generation request: {prompt[:50]}...")

        # 提交生成请求（增加超时时间）
        response = requests.post(ZIMAGE_GENERATE, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if result.get('success'):
            uuid = result.get('data', {}).get('uuid')
            if uuid:
                # 缓存任务信息
                task_cache[uuid] = {
                    'created_at': time.time(),
                    'prompt': prompt
                }
                logger.info(f"Task created: {uuid}")

                # 返回OpenAI格式的响应
                return jsonify({
                    "id": f"chatcmpl-{uuid}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "zimage",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"图片生成任务已提交，任务ID: {uuid}"
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(prompt),
                        "completion_tokens": 10,
                        "total_tokens": len(prompt) + 10
                    },
                    "task_id": uuid  # 添加任务ID
                })

        return jsonify({"error": "Failed to create generation task"}), 500

    except requests.exceptions.Timeout:
        logger.error("Timeout creating generation task")
        return jsonify({"error": "生成请求超时，请稍后重试"}), 504
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        return jsonify({"error": f"创建任务失败: {str(e)}"}), 500

@app.route('/v1/tasks/<uuid>', methods=['GET'])
def get_task_status(uuid):
    """获取任务状态"""
    try:
        # 先检查缓存
        if uuid in task_cache:
            cache_info = task_cache[uuid]
            # 如果任务刚创建不久，直接返回缓存状态
            if time.time() - cache_info['created_at'] < 5:
                return jsonify({
                    "success": True,
                    "data": {
                        "task": {
                            "taskStatus": "pending",
                            "progress": 0
                        }
                    }
                })

        # 查询实际状态（增加超时时间）
        response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=15)
        response.raise_for_status()

        result = response.json()

        # 更新缓存
        if uuid in task_cache and result.get('success'):
            task_data = result.get('data', {}).get('task', {})
            task_cache[uuid]['status'] = task_data.get('taskStatus', 'unknown')
            task_cache[uuid]['last_checked'] = time.time()

        return jsonify(result)

    except requests.exceptions.Timeout:
        # 超时返回缓存或处理中状态
        if uuid in task_cache:
            return jsonify({
                "success": True,
                "data": {
                    "task": {
                        "taskStatus": task_cache[uuid].get('status', 'processing'),
                        "progress": task_cache[uuid].get('progress', 50)
                    }
                },
                "timeout": True
            })
        return jsonify({
            "success": True,
            "data": {
                "task": {
                    "taskStatus": "processing",
                    "progress": 50
                }
            },
            "timeout": True
        })
    except Exception as e:
        logger.error(f"Error checking task {uuid}: {str(e)}")
        return jsonify({
            "success": True,  # 即使失败也返回success，避免前端错误
            "data": {
                "task": {
                    "taskStatus": "processing" if uuid in task_cache else "unknown",
                    "errorMessage": str(e)
                }
            }
        })

@app.route('/v1/images/<uuid>', methods=['GET'])
def get_image_results(uuid):
    """获取图片结果（简化版）"""
    if not uuid:
        return jsonify({"error": "No task ID provided"}), 400

    try:
        max_attempts = 40  # 增加最大尝试次数
        attempt = 0

        while attempt < max_attempts:
            try:
                response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=15)
                response.raise_for_status()

                result = response.json()

                if result.get('success'):
                    task_data = result.get('data', {}).get('task', {})
                    status = task_data.get('taskStatus')

                    if status == 'completed':
                        result_url = task_data.get('resultUrl')
                        result_urls = task_data.get('resultUrls', [])

                        images = []
                        if result_url:
                            images = [result_url]
                        elif result_urls:
                            images = result_urls

                        # 清理缓存
                        if uuid in task_cache:
                            del task_cache[uuid]

                        logger.info(f"Task {uuid} completed with {len(images)} images")

                        return jsonify({
                            "success": True,
                            "data": {
                                "images": images
                            }
                        })

                    elif status == 'failed':
                        error_msg = task_data.get('errorMessage', 'Task failed')
                        logger.error(f"Task {uuid} failed: {error_msg}")
                        return jsonify({
                            "success": False,
                            "error": error_msg
                        }), 500

                # 等待并重试
                if attempt < 10:
                    time.sleep(2)  # 前10次每2秒检查
                elif attempt < 20:
                    time.sleep(3)  # 中期每3秒检查
                else:
                    time.sleep(5)  # 后期每5秒检查

                attempt += 1
                if attempt % 5 == 0:
                    logger.info(f"Task {uuid} still processing, attempt {attempt}/{max_attempts}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout checking task {uuid}, attempt {attempt}")
                # 继续尝试
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    attempt += 1
                    continue
                else:
                    break

        # 超时处理
        logger.error(f"Task {uuid} timed out after {max_attempts} attempts")
        return jsonify({
            "success": False,
            "error": f"任务超时，已尝试 {max_attempts} 次。图片生成通常需要1-3分钟，请稍后再试。"
        }), 408

    except Exception as e:
        logger.error(f"Error getting images for task {uuid}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"获取图片失败: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8003))

    print("=" * 50)
    print("Z-Image Simple Proxy Server")
    print(f"Server running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print("=" * 50)

    # 启动keep-alive
    start_keep_alive()

    app.run(host='0.0.0.0', port=port, debug=False)