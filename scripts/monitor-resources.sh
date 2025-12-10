#!/bin/bash

# Docker容器资源监控脚本
# 使用方法: ./scripts/monitor-resources.sh [container_name]

CONTAINER_NAME=${1:-z-image-fixed}
INTERVAL=${2:-5}  # 默认5秒间隔

echo "=== Docker容器资源监控 ==="
echo "容器名称: $CONTAINER_NAME"
echo "监控间隔: ${INTERVAL}秒"
echo "按 Ctrl+C 停止监控"
echo "============================="

while true; do
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 监控容器: $CONTAINER_NAME"
    echo "----------------------------------------"

    # 检查容器是否在运行
    if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        echo "❌ 容器 $CONTAINER_NAME 未运行"
        sleep $INTERVAL
        continue
    fi

    # 获取容器ID
    CONTAINER_ID=$(docker ps -q -f name=$CONTAINER_NAME)

    echo "📊 CPU和内存使用情况:"
    docker stats $CONTAINER_ID --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

    echo ""
    echo "🔧 容器内线程和进程信息:"
    docker exec $CONTAINER_ID ps -eT 2>/dev/null | head -10 || echo "无法获取线程信息"

    echo ""
    echo "💾 内存详细信息:"
    docker exec $CONTAINER_ID cat /proc/meminfo 2>/dev/null | grep -E "(MemTotal|MemFree|MemAvailable|Active|Inactive)" || echo "无法获取内存信息"

    echo ""
    echo "🧵 线程限制信息:"
    docker exec $CONTAINER_ID cat /proc/sys/kernel/threads-max 2>/dev/null || echo "无法获取线程限制"

    echo ""
    echo "📁 文件描述符限制:"
    docker exec $CONTAINER_ID sh -c 'ulimit -n' 2>/dev/null || echo "无法获取文件描述符限制"

    echo ""
    echo "⏱️  系统负载:"
    docker exec $CONTAINER_ID cat /proc/loadavg 2>/dev/null || echo "无法获取系统负载"

    sleep $INTERVAL
done