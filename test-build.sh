#!/bin/bash

echo "测试构建不同的 Docker 版本..."

# 测试标准版本
echo "1. 构建标准版本..."
docker build -t z-image:test .
if [ $? -eq 0 ]; then
    echo "✅ 标准版本构建成功"
else
    echo "❌ 标准版本构建失败"
fi

# 测试最小版本
echo ""
echo "2. 构建最小版本..."
docker build -f Dockerfile.minimal -t z-image:minimal .
if [ $? -eq 0 ]; then
    echo "✅ 最小版本构建成功"
else
    echo "❌ 最小版本构建失败"
fi

# 测试 Alpine 版本
echo ""
echo "3. 构建 Alpine 版本..."
docker build -f Dockerfile.alpine -t z-image:alpine .
if [ $? -eq 0 ]; then
    echo "✅ Alpine 版本构建成功"
else
    echo "❌ Alpine 版本构建失败"
fi

# 显示镜像大小
echo ""
echo "镜像大小对比："
docker images | grep z-image | grep -v REPOSITORY | awk '{print $1":"$2"\t"$7}'