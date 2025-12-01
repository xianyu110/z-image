#!/bin/bash

# Docker 安装和部署脚本
# 适用于 Linux/macOS 系统

set -e

echo "🐳 Z-Image Docker 部署脚本"
echo "=========================="

# 检查是否已安装 Docker
check_docker() {
    if command -v docker &> /dev/null; then
        echo "✅ Docker 已安装"
        docker --version
        return 0
    else
        echo "❌ Docker 未安装"
        return 1
    fi
}

# 检查是否已安装 Docker Compose
check_docker_compose() {
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        echo "✅ Docker Compose 已安装"
        if command -v docker-compose &> /dev/null; then
            docker-compose --version
        else
            docker compose version
        fi
        return 0
    else
        echo "❌ Docker Compose 未安装"
        return 1
    fi
}

# 安装 Docker (Ubuntu/Debian)
install_docker_ubuntu() {
    echo "📥 正在安装 Docker..."

    # 更新包索引
    sudo apt-get update

    # 安装必要的包
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # 添加 Docker 官方 GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # 添加 Docker 仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 安装 Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # 启动 Docker 服务
    sudo systemctl start docker
    sudo systemctl enable docker

    # 将当前用户添加到 docker 组
    sudo usermod -aG docker $USER

    echo "✅ Docker 安装完成"
    echo "⚠️  请重新登录或运行 'newgrp docker' 以使用户组更改生效"
}

# 安装 Docker (macOS)
install_docker_macos() {
    echo "🍎 macOS 系统检测到"
    echo "请访问 https://www.docker.com/products/docker-desktop 下载并安装 Docker Desktop"
    echo "或者使用 Homebrew: brew install --cask docker"
}

# 构建 Docker 镜像
build_docker() {
    echo "🏗️  正在构建 Docker 镜像..."

    if docker build -t z-image-proxy .; then
        echo "✅ Docker 镜像构建成功"
        return 0
    else
        echo "❌ Docker 镜像构建失败"
        return 1
    fi
}

# 使用 Docker Compose 启动服务
start_service() {
    echo "🚀 正在启动服务..."

    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # 停止现有服务（如果存在）
    $COMPOSE_CMD down 2>/dev/null || true

    # 启动服务
    if $COMPOSE_CMD up -d; then
        echo "✅ 服务启动成功"
        echo "🌐 服务地址: http://localhost:8000"
        echo "🔍 健康检查: http://localhost:8000/api/health"

        # 等待服务启动
        echo "⏳ 等待服务启动..."
        sleep 10

        # 测试服务
        if curl -f http://localhost:8000/api/health &>/dev/null; then
            echo "✅ 服务运行正常"
        else
            echo "⚠️  服务可能需要更多时间启动"
        fi

        return 0
    else
        echo "❌ 服务启动失败"
        return 1
    fi
}

# 显示状态
show_status() {
    echo "📊 服务状态:"

    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi

    echo ""
    echo "📝 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
    echo "🔄 重启服务: docker-compose restart"
}

# 主函数
main() {
    echo "1. 检查 Docker 环境..."

    if ! check_docker; then
        echo ""
        echo "请选择 Docker 安装方式:"
        echo "1) Ubuntu/Debian 系统"
        echo "2) macOS 系统"
        echo "3) 手动安装"
        echo "4) 跳过安装"
        echo ""
        read -p "请输入选择 [1-4]: " choice

        case $choice in
            1)
                install_docker_ubuntu
                ;;
            2)
                install_docker_macos
                exit 0
                ;;
            3)
                echo "请访问 https://docs.docker.com/get-docker/ 手动安装 Docker"
                exit 0
                ;;
            4)
                echo "跳过 Docker 安装"
                exit 0
                ;;
            *)
                echo "无效选择"
                exit 1
                ;;
        esac

        echo ""
        echo "⚠️  Docker 安装完成后，请重新运行此脚本"
        exit 0
    fi

    echo ""
    check_docker_compose

    echo ""
    echo "2. 构建 Docker 镜像..."
    if ! build_docker; then
        exit 1
    fi

    echo ""
    echo "3. 启动服务..."
    if ! start_service; then
        exit 1
    fi

    echo ""
    show_status

    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "📖 使用说明:"
    echo "  - API 端点: http://localhost:8000/v1/chat/completions"
    echo "  - 健康检查: http://localhost:8000/api/health"
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
}

# 运行主函数
main "$@"