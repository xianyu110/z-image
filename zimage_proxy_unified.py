#!/usr/bin/env python3
"""
Z-Image 统一服务 - 同时提供 API 和静态文件服务
适用于 Render 免费部署
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import time
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

# 创建 Flask 应用
app = Flask(__name__, static_folder='web', static_url_path='')

# 配置 CORS - 允许所有来源
CORS(app)

# 配置日志
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
        def keep_alive():
            while True:
                try:
                    time.sleep(600)  # 10分钟
                    port = os.environ.get('PORT', 8000)
                    # 使用 render 的 URL
                    if 'RENDER_SERVICE_URL' in os.environ:
                        url = f"{os.environ['RENDER_SERVICE_URL']}/health"
                    else:
                        url = f"http://localhost:{port}/health"

                    requests.get(url, timeout=5)
                    logger.info("Keep-alive ping sent")
                except Exception as e:
                    logger.warning(f"Keep-alive ping failed: {e}")

        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        logger.info("Keep-alive service started (pinging every 10 minutes)")

# 静态文件路由 - 处理前端
@app.route('/')
def index():
    """提供前端主页"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        return jsonify({
            "service": "z-image-unified",
            "message": "Frontend not found. This is the API service.",
            "endpoints": {
                "health": "/health",
                "completions": "/v1/chat/completions",
                "task": "/v1/tasks/<taskId>",
                "image": "/v1/images/<taskId>"
            }
        })

@app.route('/<path:path>')
def static_files(path):
    """提供静态文件"""
    try:
        # 如果是API路径，跳过
        if path.startswith('v1/') or path.startswith('api/'):
            return jsonify({"error": "API endpoint not found"}), 404

        # 返回静态文件
        return send_from_directory(app.static_folder, path)
    except:
        # 文件不存在时返回404
        return jsonify({"error": "File not found"}), 404

# API 路由
@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "z-image-unified",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/v1/chat/completions', methods=['POST', 'OPTIONS'])
def chat_completions():
    """图片生成接口"""
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

        # 构建请求
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512,
            "steps": 4,
            "batch_size": 1,
            "cfg_scale": 6
        }

        logger.info(f"Submitting generation request: {prompt[:50]}...")

        # 提交生成请求
        response = requests.post(ZIMAGE_GENERATE, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        if result.get('success'):
            uuid = result.get('data', {}).get('uuid')
            if uuid:
                task_cache[uuid] = {
                    'created_at': time.time(),
                    'prompt': prompt
                }
                logger.info(f"Task created: {uuid}")

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
                    "task_id": uuid
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
        if uuid in task_cache:
            cache_info = task_cache[uuid]
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

        response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=15)
        response.raise_for_status()

        result = response.json()

        if uuid in task_cache and result.get('success'):
            task_data = result.get('data', {}).get('task', {})
            task_cache[uuid]['status'] = task_data.get('taskStatus', 'unknown')
            task_cache[uuid]['last_checked'] = time.time()

        return jsonify(result)

    except requests.exceptions.Timeout:
        if uuid in task_cache:
            return jsonify({
                "success": True,
                "data": {
                    "task": {
                        "taskStatus": task_cache[uuid].get('status', 'processing'),
                        "progress": 50
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
            "success": True,
            "data": {
                "task": {
                    "taskStatus": "processing" if uuid in task_cache else "unknown",
                    "errorMessage": str(e)
                }
            }
        })

@app.route('/v1/images/<uuid>', methods=['GET'])
def get_image_results(uuid):
    """获取图片结果"""
    if not uuid:
        return jsonify({"error": "No task ID provided"}), 400

    try:
        max_attempts = 40
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

                if attempt < 10:
                    time.sleep(2)
                elif attempt < 20:
                    time.sleep(3)
                else:
                    time.sleep(5)

                attempt += 1
                if attempt % 5 == 0:
                    logger.info(f"Task {uuid} still processing, attempt {attempt}/{max_attempts}")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout checking task {uuid}, attempt {attempt}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    attempt += 1
                    continue
                else:
                    break

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
    port = int(os.environ.get('PORT', 8000))

    print("=" * 50)
    print("Z-Image Unified Service (API + Frontend)")
    print(f"Server running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print("=" * 50)

    # 启动keep-alive
    start_keep_alive()

    # 生产环境不要使用debug
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)