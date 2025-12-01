#!/usr/bin/env python3
"""
Test client for Z-Image Proxy Server
Demonstrates how to use the OpenAI-compatible proxy
"""

import requests
import json
import time
import argparse
from typing import Optional

BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health check:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def generate_image(prompt: str, negative_prompt: str = "", batch_size: int = 1, width: int = 1024, height: int = 1024):
    """
    Generate images using the OpenAI-compatible endpoint
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
        print(f"Generating image with prompt: {prompt}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            print(f"Error: {result['error']}")
            return None

        task_uuid = result["choices"][0]["message"]["content"]
        print(f"Task submitted with UUID: {task_uuid}")
        return task_uuid

    except requests.exceptions.RequestException as e:
        print(f"Error generating image: {e}")
        return None

def get_task_status(uuid: str):
    """Check the status of a generation task"""
    try:
        response = requests.get(f"{BASE_URL}/v1/tasks/{uuid}")
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error checking task status: {e}")
        return None

def get_completed_images(uuid: str, timeout: int = 300):
    """
    Wait for images to complete and return the URLs
    """
    try:
        response = requests.get(f"{BASE_URL}/v1/images/{uuid}")
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error getting completed images: {e}")
        return None

def test_full_workflow(prompt: str, negative_prompt: str = ""):
    """Test the complete workflow from generation to completion"""
    print("\n=== Testing Full Workflow ===")

    # Step 1: Generate image
    task_uuid = generate_image(prompt, negative_prompt)
    if not task_uuid:
        print("Failed to submit generation task")
        return

    # Step 2: Wait for completion
    print(f"\nWaiting for task {task_uuid} to complete...")
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > 300:  # 5 minute timeout
            print("Timeout reached")
            break

        # Check status
        status_result = get_task_status(task_uuid)
        if status_result and status_result.get('success'):
            task_data = status_result['data']['task']
            status = task_data.get('taskStatus')
            progress = task_data.get('progress', 0)

            print(f"Status: {status}, Progress: {progress}%")

            if status == 'completed':
                print("Task completed!")
                break
            elif status == 'failed':
                print("Task failed!")
                break

        time.sleep(5)

    # Step 3: Get results
    print("\nGetting final results...")
    results = get_completed_images(task_uuid)
    if results and results.get('status') == 'completed':
        image_urls = results.get('image_urls', [])
        print(f"\nGenerated {len(image_urls)} images:")
        for i, url in enumerate(image_urls):
            print(f"  {i+1}. {url}")
    elif results:
        print(f"Error: {results.get('error', 'Unknown error')}")

def main():
    parser = argparse.ArgumentParser(description="Test client for Z-Image Proxy Server")
    parser.add_argument("--prompt", "-p", default="一只站在月球上的猫，超现实主义",
                       help="Prompt for image generation")
    parser.add_argument("--negative-prompt", "-n", default="模糊,水印",
                       help="Negative prompt for image generation")
    parser.add_argument("--batch-size", "-b", type=int, default=1,
                       help="Number of images to generate")
    parser.add_argument("--width", "-w", type=int, default=1024,
                       help="Image width")
    parser.add_argument("--height", "-H", type=int, default=1024,
                       help="Image height")
    parser.add_argument("--health", action="store_true",
                       help="Run health check only")

    args = parser.parse_args()

    if args.health:
        test_health_check()
        return

    # First check if server is running
    if not test_health_check():
        print("Server is not running. Please start the proxy server first:")
        print("python zimage_proxy.py")
        return

    print("Server is running. Starting image generation test...")

    # Test with provided arguments
    if args.batch_size > 1:
        # Generate multiple images at once
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
        # Test single image with full workflow
        test_full_workflow(args.prompt, args.negative_prompt)

if __name__ == "__main__":
    main()