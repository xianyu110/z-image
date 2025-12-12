#!/usr/bin/env python3
"""
Z-Image Proxy Server for Render deployment
支持 Flask 服务器用于 Render 等平台的部署
"""

from flask import Flask, request, jsonify, Response
import json
import time
import http.client
import urllib.parse
from typing import Dict, Any, Optional
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Z-Image API endpoints
ZIMAGE_GENERATE_HOST = "zimage.run"
ZIMAGE_GENERATE_PATH = "/api/z-image/generate"
ZIMAGE_TASK_PATH = "/api/z-image/task"

class ZImageProxy:
    def __init__(self):
        self.zimage_generate_host = ZIMAGE_GENERATE_HOST
        self.zimage_generate_path = ZIMAGE_GENERATE_PATH
        self.zimage_task_path = ZIMAGE_TASK_PATH

    def make_request(self, method: str, host: str, path: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to external API"""
        try:
            conn = http.client.HTTPSConnection(host, timeout=30)

            if method == "POST" and data:
                json_data = json.dumps(data)
                headers = {
                    'Content-Type': 'application/json',
                    'Content-Length': str(len(json_data))
                }
                conn.request("POST", path, body=json_data, headers=headers)
            else:
                conn.request("GET", path)

            response = conn.getresponse()
            response_data = response.read().decode('utf-8')

            conn.close()

            return {
                'status': response.status,
                'data': json.loads(response_data) if response_data else {}
            }

        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'status': 500,
                'data': {'error': f'Request failed: {str(e)}'}
            }

    def generate_image(self, prompt: str, extra_body: Dict) -> Dict:
        """Generate image using Z-Image API"""
        # Translate to Z-Image payload format
        zimage_payload = {
            "prompt": prompt,
            "negative_prompt": extra_body.get('negative_prompt', ''),
            "model": "turbo" if "turbo" in extra_body.get('model', '') else "base",
            "batch_size": extra_body.get('batch_size', 1),
            "width": extra_body.get('width', 1024),
            "height": extra_body.get('height', 1024),
            "steps": extra_body.get('steps', 8),
            "cfg_scale": extra_body.get('cfg_scale', 7)
        }

        logger.info(f"Forwarding request to Z-Image: {zimage_payload}")

        # Submit to Z-Image API
        result = self.make_request("POST", self.zimage_generate_host, self.zimage_generate_path, zimage_payload)

        if result['status'] != 200 or not result['data'].get('success'):
            error_msg = result['data'].get('error', 'Unknown error from Z-Image')
            logger.error(f"Z-Image API error: {error_msg}")
            return {
                "error": error_msg,
                "status": result['status']
            }

        uuid = result['data']['data']['uuid']
        logger.info(f"Task submitted successfully with UUID: {uuid}")

        # Return OpenAI-compatible response
        return {
            "success": True,
            "data": {
                "id": f"chatcmpl-{uuid}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": extra_body.get('model', 'zimage-turbo'),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": uuid,
                        "task_uuid": uuid
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        }

    def get_task_status(self, uuid: str) -> Dict:
        """Get the status of a Z-Image generation task"""
        result = self.make_request("GET", self.zimage_generate_host, f"{self.zimage_task_path}/{uuid}")

        if result['status'] != 200:
            return {
                "error": f"HTTP {result['status']}: {result['data'].get('error', 'Request failed')}",
                "status": result['status']
            }

        logger.info(f"Task status for {uuid}: {result['data']}")
        return result['data']

    def get_completed_images(self, uuid: str) -> Dict:
        """Get completed image URLs for a task (polls until completion)"""
        max_attempts = 60  # Maximum polling attempts (5 minutes with 5-second intervals)
        attempt = 0

        while attempt < max_attempts:
            status_result = self.get_task_status(uuid)

            if status_result.get('success') and status_result.get('data', {}).get('task', {}).get('taskStatus') == 'completed':
                task_data = status_result['data']['task']
                image_urls = task_data.get('resultUrls', [])

                logger.info(f"Task {uuid} completed with {len(image_urls)} images")

                return {
                    "success": True,
                    "data": {
                        "uuid": uuid,
                        "status": "completed",
                        "image_urls": image_urls,
                        "task_info": task_data
                    }
                }

            # If task failed
            if status_result.get('success') and status_result.get('data', {}).get('task', {}).get('taskStatus') == 'failed':
                logger.error(f"Task {uuid} failed")
                return {
                    "success": False,
                    "error": "Task failed to complete"
                }

            # Task still processing, wait and retry
            logger.info(f"Task {uuid} still processing, attempt {attempt + 1}/{max_attempts}")
            time.sleep(5)
            attempt += 1

        # Timeout reached
        logger.error(f"Task {uuid} timed out after {max_attempts} attempts")
        return {
            "success": False,
            "error": "Task took too long to complete",
            "status": 408
        }

# Initialize proxy instance
zimage_proxy = ZImageProxy()

@app.route('/')
def index():
    """Handle root endpoint with API information"""
    return jsonify({
        "service": "Z-Image Proxy Server",
        "version": "1.0.0",
        "description": "OpenAI-compatible proxy for Z-Image generation API",
        "endpoints": {
            "chat_completions": "/api/v1/chat/completions (POST)",
            "task_status": "/api/v1/tasks/<uuid> (GET)",
            "image_results": "/api/v1/images/<uuid> (GET)",
            "health": "/api/health (GET)"
        },
        "usage": "Send OpenAI-compatible chat completion requests to /api/v1/chat/completions"
    })

@app.route('/api/')
def api_index():
    """Handle API root endpoint"""
    return jsonify({
        "service": "Z-Image Proxy Server",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Handle health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "zimage-proxy",
        "timestamp": int(time.time())
    })

@app.route('/api/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Handle OpenAI-compatible chat completions endpoint"""
    try:
        # Parse request body
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()

        # Extract prompt from messages (OpenAI format)
        messages = data.get('messages', [])
        if not messages:
            return jsonify({"error": "No messages provided"}), 400

        prompt = messages[0].get('content')
        if not prompt or not isinstance(prompt, str):
            return jsonify({"error": "Prompt is required and must be a string"}), 400

        # Extract parameters from extra_body or use defaults
        extra_body = data.get('extra_body', {})
        extra_body['model'] = data.get('model', 'zimage-turbo')

        # Generate image
        result = zimage_proxy.generate_image(prompt, extra_body)

        if result.get('success'):
            return jsonify(result['data'])
        else:
            return jsonify({"error": result.get('error', 'Unknown error')}), result.get('status', 500)

    except Exception as e:
        logger.error(f"Chat completions error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/v1/tasks/<uuid>', methods=['GET'])
def get_task_status(uuid):
    """Handle task status check endpoint"""
    result = zimage_proxy.get_task_status(uuid)
    return jsonify(result)

@app.route('/api/v1/images/<uuid>', methods=['GET'])
def get_completed_images(uuid):
    """Handle completed images retrieval endpoint"""
    result = zimage_proxy.get_completed_images(uuid)

    if result.get('success'):
        return jsonify(result['data'])
    else:
        return jsonify({
            "error": result.get('error', 'Unknown error')
        }), result.get('status', 500)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

# For Render and other PaaS platforms
if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))

    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)