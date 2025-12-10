#!/usr/bin/env python3
"""
多线程功能测试脚本
用于验证Docker容器的线程支持能力
"""

import threading
import time
import requests
import concurrent.futures
from datetime import datetime

# 测试配置
API_BASE_URL = "http://localhost:8000"
NUM_CONCURRENT_REQUESTS = 20
TEST_DURATION = 30  # 秒

def make_request(request_id):
    """发送单个请求"""
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        end_time = time.time()

        if response.status_code == 200:
            return {
                'request_id': request_id,
                'status': 'success',
                'duration': end_time - start_time,
                'thread_id': threading.current_thread().ident
            }
        else:
            return {
                'request_id': request_id,
                'status': f'error_{response.status_code}',
                'duration': end_time - start_time,
                'thread_id': threading.current_thread().ident
            }
    except Exception as e:
        return {
            'request_id': request_id,
            'status': f'exception_{str(e)}',
            'duration': 0,
            'thread_id': threading.current_thread().ident
        }

def test_concurrent_requests():
    """测试并发请求"""
    print(f"🧪 开始并发请求测试")
    print(f"📊 并发数量: {NUM_CONCURRENT_REQUESTS}")
    print(f"⏰ 测试时长: {TEST_DURATION}秒")
    print("=" * 50)

    results = []
    start_time = time.time()
    request_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CONCURRENT_REQUESTS) as executor:
        while time.time() - start_time < TEST_DURATION:
            # 提交多个并发请求
            futures = []
            for i in range(NUM_CONCURRENT_REQUESTS):
                future = executor.submit(make_request, request_count)
                futures.append(future)
                request_count += 1

            # 收集结果
            for future in concurrent.futures.as_completed(futures, timeout=15):
                result = future.result()
                results.append(result)

                if result['status'] == 'success':
                    print(f"✅ 请求 {result['request_id']:4d}: {result['duration']:.3f}s (线程 {result['thread_id']})")
                else:
                    print(f"❌ 请求 {result['request_id']:4d}: {result['status']}")

            # 短暂休息
            time.sleep(1)

    print("=" * 50)
    print(f"📈 测试完成!")
    print(f"🔢 总请求数: {len(results)}")

    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = len(results) - success_count

    print(f"✅ 成功请求: {success_count}")
    print(f"❌ 失败请求: {error_count}")
    print(f"📊 成功率: {success_count/len(results)*100:.1f}%")

    if success_count > 0:
        avg_duration = sum(r['duration'] for r in results if r['status'] == 'success') / success_count
        print(f"⏱️  平均响应时间: {avg_duration:.3f}s")

        # 线程使用情况
        unique_threads = set(r['thread_id'] for r in results if r['status'] == 'success')
        print(f"🧵 使用的线程数: {len(unique_threads)}")

        if len(unique_threads) > 1:
            print("🎉 多线程功能正常工作!")
        else:
            print("⚠️  可能只使用了单线程")

def test_thread_creation():
    """测试线程创建能力"""
    print("\n🧪 测试线程创建能力")
    print("=" * 30)

    def dummy_task(thread_id):
        """虚拟任务"""
        time.sleep(0.1)
        return f"Thread {thread_id} completed"

    try:
        # 尝试创建多个线程
        threads = []
        start_time = time.time()

        for i in range(50):  # 尝试创建50个线程
            thread = threading.Thread(target=dummy_task, args=(i,))
            threads.append(thread)
            thread.start()

        print(f"✅ 成功创建 50 个线程")

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        end_time = time.time()
        print(f"⏱️  所有线程在 {end_time - start_time:.3f}s 内完成")
        print("🎉 线程创建和执行正常!")

    except Exception as e:
        print(f"❌ 线程创建失败: {e}")

def main():
    """主测试函数"""
    print("🔍 Docker容器多线程功能测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 测试目标: {API_BASE_URL}")
    print()

    # 首先测试服务是否可用
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务不可用: HTTP {response.status_code}")
            return
        print("✅ 服务可用，开始测试...")
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return

    # 执行测试
    test_thread_creation()
    test_concurrent_requests()

if __name__ == "__main__":
    main()