# Z-Image Docker 部署 Makefile

.PHONY: help build run stop logs clean test status install-docker

# 默认目标
help: ## 显示帮助信息
	@echo "Z-Image Docker 部署命令"
	@echo "====================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-docker: ## 安装 Docker (仅限 Ubuntu/Debian)
	@echo "📥 安装 Docker..."
	@./scripts/docker-setup.sh

build: ## 构建 Docker 镜像
	@echo "🏗️  构建 Docker 镜像..."
	docker build -t z-image-proxy .

build-simple: ## 构建简化版 Docker 镜像 (Alpine)
	@echo "🏗️  构建简化版 Docker 镜像 (Alpine Linux)..."
	docker build -f Dockerfile.simple -t z-image-proxy-simple .

run: ## 运行容器 (后台)
	@echo "🚀 启动服务..."
	docker-compose up -d

run-simple: ## 运行简化版容器
	@echo "🚀 启动简化版服务..."
	docker-compose -f docker-compose.simple.yml up -d

run-frontend: ## 运行容器 (前台显示日志)
	@echo "🚀 启动服务 (前台)..."
	docker-compose up

stop: ## 停止服务
	@echo "🛑 停止服务..."
	docker-compose down

restart: ## 重启服务
	@echo "🔄 重启服务..."
	docker-compose restart

logs: ## 查看服务日志
	@echo "📝 查看日志..."
	docker-compose logs -f

status: ## 查看服务状态
	@echo "📊 服务状态:"
	docker-compose ps

test: ## 测试 API 服务
	@echo "🧪 测试服务..."
	@curl -f http://localhost:8000/api/health || echo "❌ 健康检查失败，服务可能未启动"

test-api: ## 测试图片生成 API
	@echo "🖼️  测试图片生成 API..."
	@curl -X POST http://localhost:8000/v1/chat/completions \
		-H "Content-Type: application/json" \
		-d '{
			"model": "zimage-turbo",
			"messages": [{"role": "user", "content": "一只可爱的猫"}],
			"extra_body": {
				"batch_size": 1,
				"width": 512,
				"height": 512
			}
		}' || echo "❌ API 测试失败"

clean: ## 清理 Docker 资源
	@echo "🧹 清理 Docker 资源..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

rebuild: ## 重新构建并运行
	@echo "🔧 重新构建并运行..."
	$(MAKE) stop
	$(MAKE) build
	$(MAKE) run

dev: ## 开发模式 (构建并运行)
	@echo "🛠️  开发模式..."
	$(MAKE) build
	$(MAKE) run-frontend

# 开发者命令
shell: ## 进入容器 shell
	docker exec -it z-image-proxy /bin/bash

inspect: ## 检查容器
	docker inspect z-image-proxy

stats: ## 查看 Docker 统计
	docker stats z-image-proxy

# 生产部署
deploy-prod: ## 生产环境部署
	@echo "🚀 生产环境部署..."
	docker-compose -f docker-compose.yml up -d --build

deploy-dev: ## 开发环境部署
	@echo "🛠️  开发环境部署..."
	docker-compose -f docker-compose.yml up -d --build

# 版本信息
version: ## 显示 Docker 版本
	@echo "Docker 版本:"
	@docker --version
	@echo ""
	@echo "Docker Compose 版本:"
	@if command -v docker-compose &> /dev/null; then \
		docker-compose --version; \
	else \
		docker compose version; \
	fi

# 快速开始
quickstart: ## 快速开始 (构建 + 运行)
	@echo "⚡ 快速开始..."
	$(MAKE) build
	$(MAKE) run
	@sleep 10
	$(MAKE) status
	@echo ""
	@echo "✅ 部署完成！"
	@echo "🌐 API 地址: http://localhost:8000"
	@echo "🔍 健康检查: http://localhost:8000/api/health"