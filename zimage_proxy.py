from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import requests
import time
import logging
from typing import Dict, Any, Optional

app = Flask(__name__)
CORS(app)  # 启用 CORS 支持

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Z-Image API endpoints
ZIMAGE_GENERATE = "https://zimage.run/api/z-image/generate"
ZIMAGE_TASK = "https://zimage.run/api/z-image/task"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI-compatible chat completions endpoint that forwards requests to Z-Image API
    """
    try:
        data = request.json

        # Extract prompt from messages (OpenAI format)
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        prompt = messages[0].get('content')
        if not prompt or not isinstance(prompt, str):
            return jsonify({"error": "Prompt is required and must be a string"}), 400

        # Extract parameters from extra_body or use defaults
        extra_body = data.get('extra_body', {})

        # Translate to Z-Image payload format
        zimage_payload = {
            "prompt": prompt,
            "negative_prompt": extra_body.get('negative_prompt', ''),
            "model": "turbo" if "turbo" in data.get('model', '') else "base",
            "batch_size": extra_body.get('batch_size', 1),
            "width": extra_body.get('width', 1024),
            "height": extra_body.get('height', 1024),
            "steps": extra_body.get('steps', 8),
            "cfg_scale": extra_body.get('cfg_scale', 7)
        }

        logger.info(f"Forwarding request to Z-Image: {zimage_payload}")

        # Submit to Z-Image API
        response = requests.post(ZIMAGE_GENERATE, json=zimage_payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error from Z-Image')
            logger.error(f"Z-Image API error: {error_msg}")
            return jsonify({"error": error_msg}), response.status_code

        uuid = result['data']['uuid']
        logger.info(f"Task submitted successfully with UUID: {uuid}")

        # Return OpenAI-compatible response
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
                    "task_uuid": uuid  # Additional field for easier access
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error when calling Z-Image API: {str(e)}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/v1/tasks/<uuid>', methods=['GET'])
def get_task_status(uuid: str):
    """
    Get the status of a Z-Image generation task
    """
    try:
        response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=30)
        response.raise_for_status()

        result = response.json()
        logger.info(f"Task status for {uuid}: {result}")

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error when checking task status: {str(e)}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error when checking task status: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/v1/images/<uuid>', methods=['GET'])
def get_image_results(uuid: str):
    """
    Get completed image URLs for a task (polls until completion)
    """
    # 检查 UUID 是否为空或无效
    if not uuid or uuid.lower() == 'null' or uuid == 'None':
        return jsonify({
            "error": "Invalid task UUID",
            "message": "UUID cannot be null or empty"
        }), 400

    try:
        max_attempts = 60  # Maximum polling attempts (5 minutes with 5-second intervals)
        attempt = 0

        while attempt < max_attempts:
            response = requests.get(f"{ZIMAGE_TASK}/{uuid}", timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('success') and result.get('data', {}).get('task', {}).get('taskStatus') == 'completed':
                task_data = result['data']['task']
                # 检查是否有图片结果
                result_url = task_data.get('resultUrl')
                image_urls = [result_url] if result_url else task_data.get('resultUrls', [])

                logger.info(f"Task {uuid} completed with {len(image_urls)} images")

                return jsonify({
                    "uuid": uuid,
                    "status": "completed",
                    "image_urls": image_urls,
                    "task_info": task_data
                })

            # If task failed
            if result.get('success') and result.get('data', {}).get('task', {}).get('taskStatus') == 'failed':
                logger.error(f"Task {uuid} failed")
                return jsonify({
                    "uuid": uuid,
                    "status": "failed",
                    "error": "Task failed to complete"
                }), 500

            # Task still processing, wait and retry
            logger.info(f"Task {uuid} still processing, attempt {attempt + 1}/{max_attempts}")
            time.sleep(5)
            attempt += 1

        # Timeout reached
        logger.error(f"Task {uuid} timed out after {max_attempts} attempts")
        return jsonify({
            "uuid": uuid,
            "status": "timeout",
            "error": "Task took too long to complete"
        }), 408

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error when polling for images: {str(e)}")
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error when polling for images: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "service": "zimage-proxy",
        "timestamp": int(time.time())
    })

@app.route('/')
def index():
    """
    Root endpoint - serve optimized web interface
    """
    try:
        return send_from_directory('web', 'index_optimized.html')
    except FileNotFoundError:
        # Fallback to API info if optimized frontend not found
        return jsonify({
            "service": "Z-Image Proxy Server",
            "version": "1.0.0",
            "description": "OpenAI-compatible proxy for Z-Image generation API",
            "endpoints": {
                "chat_completions": "/v1/chat/completions (POST)",
                "task_status": "/v1/tasks/<uuid> (GET)",
                "image_results": "/v1/images/<uuid> (GET)",
                "health": "/health (GET)",
                "web_interface": "/"
            },
            "usage": "Send OpenAI-compatible chat completion requests to /v1/chat/completions"
        })

@app.route('/<path:filename>')
def static_files(filename):
    """
    Serve static files from web directory
    """
    return send_from_directory('web', filename)

@app.route('/api')
def api_info():
    """
    API information endpoint
    """
    return jsonify({
        "service": "Z-Image Proxy Server",
        "version": "1.0.0",
        "description": "OpenAI-compatible proxy for Z-Image generation API",
        "endpoints": {
            "chat_completions": "/v1/chat/completions (POST)",
            "task_status": "/v1/tasks/<uuid> (GET)",
            "image_results": "/v1/images/<uuid> (GET)",
            "health": "/health (GET)",
            "api_info": "/api",
            "web_interface": "/"
        },
        "presets": {
            "fast": {"batch_size": 1, "width": 512, "height": 512, "steps": 4, "time": "2-3s"},
            "balanced": {"batch_size": 2, "width": 768, "height": 768, "steps": 6, "time": "4-6s"},
            "quality": {"batch_size": 4, "width": 1024, "height": 1024, "steps": 8, "time": "8-12s"}
        }
    })

if __name__ == '__main__':
    port = 8001
    logger.info(f"Starting Z-Image Proxy Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)