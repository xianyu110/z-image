from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from collections import defaultdict, deque
import requests
import time
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import threading

app = Flask(__name__)
CORS(app)  # 启用 CORS 支持

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Z-Image API endpoints
ZIMAGE_GENERATE = "https://zimage.run/api/z-image/generate"
ZIMAGE_TASK = "https://zimage.run/api/z-image/task"

# 配置参数
RATE_LIMIT_REQUESTS = 10  # 每分钟最多请求数
RATE_LIMIT_WINDOW = 60    # 时间窗口（秒）
DAILY_REQUEST_LIMIT = 100  # 每日请求限制

# 内存中的数据存储
user_requests = defaultdict(lambda: deque())  # 用于频率限制
daily_usage = defaultdict(int)  # 每日使用量
usage_logs = []  # 详细使用日志
prompt_stats = defaultdict(int)  # 提示词统计
ip_stats = defaultdict(int)  # IP访问统计

# 锁对象，用于线程安全
stats_lock = threading.Lock()

def get_client_ip():
    """获取客户端真实IP"""
    # 检查代理头
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def check_rate_limit(ip: str) -> Tuple[bool, str]:
    """检查频率限制"""
    now = time.time()

    # 清理过期的请求记录
    with stats_lock:
        while user_requests[ip] and user_requests[ip][0] < now - RATE_LIMIT_WINDOW:
            user_requests[ip].popleft()

        # 检查当前窗口内的请求数
        if len(user_requests[ip]) >= RATE_LIMIT_REQUESTS:
            return False, f"Rate limit exceeded. Max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"

        # 记录当前请求
        user_requests[ip].append(now)

        # 检查每日限制
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = f"{ip}:{today}"
        if daily_usage[daily_key] >= DAILY_REQUEST_LIMIT:
            return False, f"Daily limit exceeded. Max {DAILY_REQUEST_LIMIT} requests per day"

        daily_usage[daily_key] += 1
        return True, ""

def log_usage(ip: str, prompt: str, task_uuid: str, model: str, parameters: dict, success: bool = True, error: str = None):
    """记录使用情况"""
    with stats_lock:
        # 记录到详细日志
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,  # 截断长提示
            "task_uuid": task_uuid,
            "model": model,
            "parameters": parameters,
            "success": success,
            "error": error,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "hour": datetime.now().hour
        }
        usage_logs.append(log_entry)

        # 更新统计信息
        if success:
            prompt_stats[prompt[:50]] += 1  # 使用前50个字符作为统计键
            ip_stats[ip] += 1

        # 保持日志文件在合理大小（最多10000条记录）
        if len(usage_logs) > 10000:
            usage_logs[:] = usage_logs[-5000:]

def get_usage_stats():
    """获取使用统计"""
    with stats_lock:
        today = datetime.now().strftime('%Y-%m-%d')
        today_requests = [log for log in usage_logs if log["date"] == today]

        # 按小时统计
        hourly_stats = defaultdict(int)
        successful_requests = 0
        failed_requests = 0

        for log in today_requests:
            hourly_stats[log["hour"]] += 1
            if log["success"]:
                successful_requests += 1
            else:
                failed_requests += 1

        # 最受欢迎的提示词
        top_prompts = sorted(prompt_stats.items(), key=lambda x: x[1], reverse=True)[:5]

        # 活跃IP统计
        active_ips = len(ip_stats)

        return {
            "today": {
                "total_requests": len(today_requests),
                "successful": successful_requests,
                "failed": failed_requests,
                "hourly_distribution": dict(hourly_stats)
            },
            "top_prompts": [{"prompt": k, "count": v} for k, v in top_prompts],
            "active_users": active_ips,
            "rate_limits": {
                "requests_per_minute": RATE_LIMIT_REQUESTS,
                "daily_limit": DAILY_REQUEST_LIMIT
            }
        }

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """
    OpenAI-compatible chat completions endpoint that forwards requests to Z-Image API
    """
    client_ip = get_client_ip()
    task_uuid = None
    start_time = time.time()

    try:
        # 检查频率限制
        allowed, limit_message = check_rate_limit(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {limit_message}")
            return jsonify({
                "error": "Rate limit exceeded",
                "message": limit_message,
                "retry_after": RATE_LIMIT_WINDOW
            }), 429

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

        logger.info(f"[{client_ip}] Forwarding request to Z-Image: {zimage_payload}")

        # Submit to Z-Image API
        response = requests.post(ZIMAGE_GENERATE, json=zimage_payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error from Z-Image')
            logger.error(f"[{client_ip}] Z-Image API error: {error_msg}")
            log_usage(client_ip, prompt, None, data.get('model', 'zimage-turbo'), zimage_payload, False, error_msg)
            return jsonify({"error": error_msg}), response.status_code

        task_uuid = result['data']['uuid']
        processing_time = time.time() - start_time

        logger.info(f"[{client_ip}] Task submitted successfully with UUID: {task_uuid} (took {processing_time:.2f}s)")

        # 记录成功的使用情况
        log_usage(client_ip, prompt, task_uuid, data.get('model', 'zimage-turbo'), zimage_payload, True)

        # Return OpenAI-compatible response
        return jsonify({
            "id": f"chatcmpl-{task_uuid}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data.get('model', 'zimage-turbo'),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": task_uuid,
                    "task_uuid": task_uuid  # Additional field for easier access
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "rate_limit": {
                "remaining": max(0, RATE_LIMIT_REQUESTS - len(user_requests[client_ip])),
                "reset_time": int(start_time + RATE_LIMIT_WINDOW),
                "daily_remaining": max(0, DAILY_REQUEST_LIMIT - daily_usage[f"{client_ip}:{datetime.now().strftime('%Y-%m-%d')}"])
            }
        })

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(f"[{client_ip}] {error_msg}")
        log_usage(client_ip, prompt if 'prompt' in locals() else "Unknown", task_uuid, data.get('model', 'zimage-turbo') if 'data' in locals() else "unknown", {}, False, error_msg)
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error(f"[{client_ip}] Unexpected error: {str(e)}")
        log_usage(client_ip, prompt if 'prompt' in locals() else "Unknown", task_uuid, data.get('model', 'zimage-turbo') if 'data' in locals() else "unknown", {}, False, error_msg)
        return jsonify({"error": error_msg}), 500

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

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """
    管理员统计接口 - 获取详细的使用统计
    """
    try:
        stats = get_usage_stats()

        # 添加系统信息
        client_ip = get_client_ip()
        with stats_lock:
            current_user_requests = len(user_requests[client_ip])
            user_daily_requests = daily_usage.get(f"{client_ip}:{datetime.now().strftime('%Y-%m-%d')}", 0)

        stats['current_user'] = {
            "ip": client_ip,
            "current_requests": current_user_requests,
            "daily_requests": user_daily_requests,
            "rate_limit_remaining": max(0, RATE_LIMIT_REQUESTS - current_user_requests),
            "daily_limit_remaining": max(0, DAILY_REQUEST_LIMIT - user_daily_requests)
        }

        # 添加系统性能指标
        total_memory_usage = len(usage_logs)
        stats['system'] = {
            "total_logs": total_memory_usage,
            "active_ips_tracked": len(user_requests),
            "uptime": "Available if you add uptime tracking",
            "rate_limits_enabled": True
        }

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        return jsonify({"error": "Failed to get statistics"}), 500

@app.route('/admin/logs', methods=['GET'])
def admin_logs():
    """
    管理员日志接口 - 获取最近的请求日志
    """
    try:
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        success_only = request.args.get('success_only', 'false').lower() == 'true'

        # 验证参数
        if limit > 1000:
            limit = 1000  # 最大限制
        if limit < 1:
            limit = 50

        with stats_lock:
            # 过滤日志
            filtered_logs = usage_logs
            if success_only:
                filtered_logs = [log for log in usage_logs if log.get('success', False)]

            # 应用分页
            total = len(filtered_logs)
            paginated_logs = filtered_logs[offset:offset + limit]

        return jsonify({
            "logs": paginated_logs,
            "pagination": {
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total
            },
            "filters": {
                "success_only": success_only
            }
        })

    except Exception as e:
        logger.error(f"Error getting admin logs: {str(e)}")
        return jsonify({"error": "Failed to get logs"}), 500

@app.route('/admin/prompts', methods=['GET'])
def admin_prompts():
    """
    管理员提示词分析接口 - 获取热门提示词统计
    """
    try:
        # 获取查询参数
        min_count = request.args.get('min_count', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        with stats_lock:
            # 按使用次数排序
            sorted_prompts = sorted(prompt_stats.items(), key=lambda x: x[1], reverse=True)

            # 过滤和限制
            filtered_prompts = [
                {"prompt": prompt, "count": count}
                for prompt, count in sorted_prompts
                if count >= min_count
            ][:limit]

        return jsonify({
            "top_prompts": filtered_prompts,
            "total_unique_prompts": len(prompt_stats),
            "filters": {
                "min_count": min_count,
                "limit": limit
            }
        })

    except Exception as e:
        logger.error(f"Error getting prompt stats: {str(e)}")
        return jsonify({"error": "Failed to get prompt statistics"}), 500

@app.route('/admin/clear-cache', methods=['POST'])
def admin_clear_cache():
    """
    管理员清理缓存接口 - 清理旧的统计数据
    """
    try:
        # 获取清理天数参数
        days = request.args.get('days', 7, type=int)

        cutoff_date = datetime.now() - timedelta(days=days)

        with stats_lock:
            # 清理旧的日志记录
            original_count = len(usage_logs)
            usage_logs[:] = [
                log for log in usage_logs
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff_date
            ]

            # 清理旧的每日使用记录
            old_daily_keys = [
                key for key in daily_usage.keys()
                if datetime.strptime(key.split(':')[1], '%Y-%m-%d') < cutoff_date.date()
            ]
            for key in old_daily_keys:
                del daily_usage[key]

        return jsonify({
            "message": "Cache cleared successfully",
            "removed_logs": original_count - len(usage_logs),
            "remaining_logs": len(usage_logs),
            "cutoff_days": days
        })

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({"error": "Failed to clear cache"}), 500

# 添加简单的管理员认证装饰器（可选）
def require_admin_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 这里可以添加简单的认证逻辑
        # 例如：检查特定的API密钥或IP地址
        auth_header = request.headers.get('Authorization')
        if auth_header != 'Bearer zimage-admin-token':  # 简单的token认证
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 应用认证到管理员端点（可选）
# admin_stats = require_admin_auth(admin_stats)
# admin_logs = require_admin_auth(admin_logs)
# admin_prompts = require_admin_auth(admin_prompts)
# admin_clear_cache = require_admin_auth(admin_clear_cache)

if __name__ == '__main__':
    port = 8001
    logger.info(f"Starting Z-Image Proxy Server on port {port}")
    logger.info(f"Rate limits: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s, {DAILY_REQUEST_LIMIT} per day")
    logger.info("Admin endpoints available:")
    logger.info("  GET /admin/stats - Usage statistics")
    logger.info("  GET /admin/logs - Request logs")
    logger.info("  GET /admin/prompts - Popular prompts")
    logger.info("  POST /admin/clear-cache - Clear old data")
    app.run(host='0.0.0.0', port=port, debug=True)