#!/usr/bin/env python3
"""
Z-Image 代理服务器测试客户端
演示如何使用兼容 OpenAI 格式的代理服务器
"""

import requests
import json
import time
import argparse
from typing import Optional

BASE_URL = "http://localhost:8001"

def test_health_check():
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health check:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def generate_image(prompt: str, negative_prompt: str = "", batch_size: int = 1, width: int = 1024, height: int = 1024):
    """
    使用 OpenAI 兼容端点生成图片
    """
    url = f"{BASE_URL}/v1/chat/completions"

    payload = {
        "model": "zimage-turbo",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "extra_body": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "batch_size": batch_size,
            "width": width,
            "height": height,
            "steps": 8,
            "cfg_scale": 7
        }
    }

    headers = {
        "Authorization": "Bearer zimage-free",
        "Content-Type": "application/json"
    }

    try:
        print(f"正在生成图片，提示词: {prompt}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            print(f"错误: {result['error']}")
            return None

        task_uuid = result["choices"][0]["message"]["content"]
        print(f"任务已提交，UUID: {task_uuid}")
        return task_uuid

    except requests.exceptions.RequestException as e:
        print(f"生成图片时出错: {e}")
        return None

def get_task_status(uuid: str):
    """检查生成任务的状态"""
    try:
        response = requests.get(f"{BASE_URL}/v1/tasks/{uuid}")
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"检查任务状态时出错: {e}")
        return None

def get_completed_images(uuid: str, timeout: int = 300):
    """
    等待图片完成并返回 URL
    """
    try:
        response = requests.get(f"{BASE_URL}/v1/images/{uuid}")
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"获取完成图片时出错: {e}")
        return None

def test_full_workflow(prompt: str, negative_prompt: str = ""):
    """测试从生成到完成的完整工作流程"""
    print("\n=== 测试完整工作流程 ===")

    # 第一步：生成图片
    task_uuid = generate_image(prompt, negative_prompt)
    if not task_uuid:
        print("提交生成任务失败")
        return

    # 第二步：等待完成
    print(f"\n正在等待任务 {task_uuid} 完成...")
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > 300:  # 5分钟超时
            print("达到超时时间")
            break

        # 检查状态
        status_result = get_task_status(task_uuid)
        if status_result and status_result.get('success'):
            task_data = status_result['data']['task']
            status = task_data.get('taskStatus')
            progress = task_data.get('progress', 0)

            print(f"状态: {status}, 进度: {progress}%")

            if status == 'completed':
                print("任务已完成！")
                break
            elif status == 'failed':
                print("任务失败！")
                break

        time.sleep(5)

    # 第三步：获取结果
    print("\n正在获取最终结果...")
    results = get_completed_images(task_uuid)
    if results and results.get('status') == 'completed':
        image_urls = results.get('image_urls', [])
        print(f"\n已生成 {len(image_urls)} 张图片:")
        for i, url in enumerate(image_urls):
            print(f"  {i+1}. {url}")
    elif results:
        print(f"错误: {results.get('error', '未知错误')}")

def main():
    parser = argparse.ArgumentParser(description="Z-Image 代理服务器测试客户端")
    parser.add_argument("--prompt", "-p", default="一只站在���球上的猫，超现实主义",
                       help="图片生成提示词")
    parser.add_argument("--negative-prompt", "-n", default="模糊,水印",
                       help="负面提示词")
    parser.add_argument("--batch-size", "-b", type=int, default=1,
                       help="生成图片数量")
    parser.add_argument("--width", "-w", type=int, default=1024,
                       help="图片宽度")
    parser.add_argument("--height", "-H", type=int, default=1024,
                       help="图片高度")
    parser.add_argument("--health", action="store_true",
                       help="仅运行健康检查")

    args = parser.parse_args()

    if args.health:
        test_health_check()
        return

    # 首先检查服务器是否运行
    if not test_health_check():
        print("服务器未运行。请先启动代理服务器:")
        print("python3 zimage_proxy.py")
        return

    print("服务器正在运行。开始图片生成测试...")

    # 使用提供的参数进行测试
    if args.batch_size > 1:
        # 一次生成多张图片
        task_uuid = generate_image(
            args.prompt,
            args.negative_prompt,
            args.batch_size,
            args.width,
            args.height
        )
        if task_uuid:
            test_full_workflow(args.prompt, args.negative_prompt)
    else:
        # 测试单张图片的完整工作流程
        test_full_workflow(args.prompt, args.negative_prompt)

if __name__ == "__main__":
    main()