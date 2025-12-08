from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import logging
import asyncio
import threading
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import queue

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Z-Image API endpoints
ZIMAGE_GENERATE = "https://zimage.run/api/z-image/generate"
ZIMAGE_TASK = "https://zimage.run/api/z-image/task"

# Thread pool for concurrent requests
executor = ThreadPoolExecutor(max_workers=10)

# Cache for task results
task_cache = {}
cache_lock = threading.Lock()

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    优化版本：支持快速参数预设
    """
    try:
        data = request.json

        # 提取预设模式
        preset = data.get('preset', 'balanced')  # fast, balanced, quality
        custom_params = data.get('extra_body', {})

        # 根据预设设置参数
        preset_configs = {
            'fast': {
                'batch_size': 1,
                'width': 512,
                'height': 512,
                'steps': 4,
                'cfg_scale': 5,
                'negative_prompt': ''
            },
            'balanced': {
                'batch_size': 2,
                'width': 768,
                'height': 768,
                'steps': 6,
                'cfg_scale': 7,
                'negative_prompt': 'low quality, blurry'
            },
            'quality': {
                'batch_size': 4,
                'width': 1024,
                'height': 1024,
                'steps': 8,
                'cfg_scale': 8,
                'negative_prompt': 'low quality, blurry, deformed'
            }
        }

        # 合并预设和自定义参数
        config = preset_configs.get(preset, preset_configs['balanced'])
        config.update(custom_params)

        # 提取prompt
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        prompt = messages[0].get('content')
        if not prompt or not isinstance(prompt, str):
            return jsonify({"error": "Prompt is required and must be a string"}), 8

        # 构建��化的请求载荷
        zimage_payload = {
            "prompt": prompt,
            "negative_prompt": config.get('negative_prompt', ''),
            "model": "turbo" if "turbo" in data.get('model', '') else "base",
            "batch_size": config.get('batch_size', 1),
            "width": config.get('width', 512),
            "height": config.get('height', 512),
            "steps": config.get('steps', 4),
            "cfg_scale": config.get('cfg_scale', 6)
        }

        logger.info(f"Fast submit with preset '{preset}': {zimage_payload}")

        # 提交到Z-Image
        response = requests.post(ZIMAGE_GENERATE, json=zimage_payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error from Z-Image')
            logger.error(f"Z-Image API error: {error_msg}")
            return jsonify({"error": error_msg}), response.status_code

        uuid = result['data']['uuid']

        # 缓存任务信息
        with cache_lock:
            task_cache[uuid] = {
                'created_at': time.time(),
                'status': 'pending',
                'preset': preset
            }

        # 返回优化的响应
        return jsonify({
            "id": f"chatcmpl-{uuid}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data.get('model', 'zimage-turbo'),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": uuid,
                    "task_uuid": uuid,
                    "preset": preset,
                    "estimated_time": f"{2 + config.get('batch_size', 1) * config.get('steps', 4) // 2}s"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        })

    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/v1/tasks/<uuid>', methods=['GET'])
def get_task_status(uuid: str):
    """
    优化版本：支持缓存和更快的检查
    """
    try:
        # 先检查缓存
        with cache_lock:
            if uuid in task_cache:
                cached_info = task_cache[uuid]
                # 如果缓存时间很短，直接返回缓存状态
                if time.time() - cached_info['created_at'] < 2:
                    return jsonify({
                        "uuid": uuid,
                        "status": cached_info['status'],
                        "cached": True
                    })

        # 调用实际API
        try:
            response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=10)
            response.raise_for_status()
            result = response.json()

            # 更新缓存
            with cache_lock:
                if uuid in task_cache:
                    task_cache[uuid].update({
                        'status': result.get('data', {}).get('task', {}).get('taskStatus', 'unknown'),
                        'last_checked': time.time()
                    })

            return jsonify(result)
        except requests.exceptions.Timeout:
            # 超时时不返回500，而是返回缓存状态
            with cache_lock:
                if uuid in task_cache:
                    cached_info = task_cache[uuid]
                    return jsonify({
                        "uuid": uuid,
                        "status": cached_info.get('status', 'processing'),
                        "timeout": True,
                        "message": "Request timed out, returning cached status"
                    })
            # 如果没有缓存，返回处理中状态
            return jsonify({
                "uuid": uuid,
                "status": "processing",
                "timeout": True,
                "message": "Request timed out, task may still be processing"
            })

    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        # 检查是否有缓存可用
        with cache_lock:
            if uuid in task_cache:
                cached_info = task_cache[uuid]
                return jsonify({
                    "uuid": uuid,
                    "status": cached_info.get('status', 'unknown'),
                    "error": f"Network error: {str(e)}",
                    "cached": True
                })
        return jsonify({"error": f"Network error: {str(e)}"}), 500

@app.route('/v1/images/<uuid>', methods=['GET'])
def get_image_results_optimized(uuid: str):
    """
    优化版本：智能轮询，减少API调用次数
    """
    if not uuid or uuid.lower() == 'null' or uuid == 'None':
        return jsonify({"error": "Invalid task UUID"}), 400

    try:
        max_attempts = 30  # 减少最大尝试次数
        base_interval = 2  # 减少基础间隔时间
        attempt = 0

        while attempt < max_attempts:
            try:
                response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=10)
                response.raise_for_status()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout checking task {uuid}, attempt {attempt}/{max_attempts}")
                # 不立即失败，继续尝试
                if attempt < max_attempts - 1:
                    time.sleep(base_interval)
                    attempt += 1
                    continue
                else:
                    # 最后一次尝试，检查缓存
                    with cache_lock:
                        if uuid in task_cache and task_cache[uuid].get('status') == 'completed':
                            logger.info(f"Returning cached completion for task {uuid}")
                            return jsonify({
                                "uuid": uuid,
                                "status": "completed",
                                "cached": True
                            })
                    raise

            result = response.json()

            if result.get('success'):
                task_data = result.get('data', {}).get('task', {})
                status = task_data.get('taskStatus')

                if status == 'completed':
                    result_url = task_data.get('resultUrl')
                    image_urls = [result_url] if result_url else task_data.get('resultUrls', [])

                    # 清理缓存
                    with cache_lock:
                        if uuid in task_cache:
                            del task_cache[uuid]

                    logger.info(f"Task {uuid} completed with {len(image_urls)} images")

                    return jsonify({
                        "success": True,
                        "data": {
                            "images": image_urls
                        },
                        "uuid": uuid,
                        "status": "completed",
                        "task_info": task_data,
                        "total_time": attempt * base_interval
                    })

                elif status == 'failed':
                    logger.error(f"Task {uuid} failed")
                    return jsonify({
                        "uuid": uuid,
                        "status": "failed",
                        "error": "Task failed to complete"
                    }), 500

            # 智能等待：前期更频繁，后期减少频率
            if attempt < 5:
                time.sleep(1)  # 前5次每秒检查
            elif attempt < 15:
                time.sleep(2)  # 中期每2秒检查
            else:
                time.sleep(3)  # 后期每3秒检查

            attempt += 1
            logger.info(f"Task {uuid} still processing, attempt {attempt}/{max_attempts}")

        # 超时处理
        logger.error(f"Task {uuid} timed out after {max_attempts} attempts")
        return jsonify({
            "uuid": uuid,
            "status": "timeout",
            "error": "Task took too long to complete"
        }), 408

    except Exception as e:
        logger.error(f"Error polling for images: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/v1/fast-generate', methods=['POST'])
def fast_generate():
    """
    极速生成端点：最小参数，最快速度
    """
    try:
        data = request.json
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # 极速参数
        fast_payload = {
            "prompt": prompt,
            "negative_prompt": "",
            "model": "turbo",
            "batch_size": 1,
            "width": 512,
            "height": 512,
            "steps": 4,
            "cfg_scale": 5
        }

        response = requests.post(ZIMAGE_GENERATE, json=fast_payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if not result.get('success'):
            return jsonify({"error": result.get('error', 'Generation failed')}), 500

        uuid = result['data']['uuid']

        # 直接等待完成（简化版本）
        for i in range(10):  # 最多等待10秒
            time.sleep(1)
            status_resp = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=5)
            if status_resp.json().get('data', {}).get('task', {}).get('taskStatus') == 'completed':
                task_data = status_resp.json()['data']['task']
                result_url = task_data.get('resultUrl')
                image_urls = [result_url] if result_url else task_data.get('resultUrls', [])
                return jsonify({
                    "uuid": uuid,
                    "status": "completed",
                    "image_urls": image_urls,
                    "fast_mode": True
                })

        return jsonify({"uuid": uuid, "status": "processing", "message": "Check back in 2-3 seconds"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "zimage-proxy-optimized",
        "version": "2.0.0",
        "features": ["fast_presets", "smart_polling", "task_caching"]
    })

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "service": "Z-Image Proxy Server (Optimized)",
        "version": "2.0.0",
        "description": "High-performance OpenAI-compatible proxy for Z-Image generation",
        "endpoints": {
            "chat_completions": "/v1/chat/completions (POST) - 支持预设模式",
            "fast_generate": "/v1/fast-generate (POST) - 极速生成",
            "task_status": "/v1/tasks/<uuid> (GET) - 任务状态（支持缓存）",
            "image_results": "/v1/images/<uuid> (GET) - 智能轮询",
            "health": "/health (GET)"
        },
        "presets": {
            "fast": "最快速度 (512x512, 4步)",
            "balanced": "平衡模式 (768x768, 6步)",
            "quality": "高质量 (1024x1024, 8步)"
        }
    })

if __name__ == '__main__':
    port = 8002
    logger.info(f"Starting Optimized Z-Image Proxy Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)