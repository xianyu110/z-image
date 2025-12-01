# Docker 容器化部署指南

使用 Docker 容器化技术部署 Z-Image 图片生成代理服务器的完整指南。

## 📋 前置要求

### 系统要求
- Docker Engine 20.10+
- Docker Compose 2.0+（推荐）
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

### 安装 Docker

#### Ubuntu/Debian
```bash
# 更新包索引
sudo apt-get update

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get install docker-compose-plugin

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL/Fedora
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### macOS
```bash
# 使用 Homebrew 安装
brew install --cask docker

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop
```

#### Windows
```powershell
# 使用 Chocolatey 安装
choco install docker-desktop

# 或下载 Docker Desktop
# https://www.docker.com/products/docker-desktop
```

## 🚀 快速开始

### 方法一：使用 Docker Compose（推荐）

1. **克隆仓库**
   ```bash
   git clone https://github.com/xianyu110/z-image.git
   cd z-image
   ```

2. **启动服务**
   ```bash
   # 构建并启动容器（后台运行）
   docker-compose up -d

   # 或者前台运行（查看实时日志）
   docker-compose up
   ```

3. **验证部署**
   ```bash
   # 检查容器状态
   docker-compose ps

   # 查看日志
   docker-compose logs -f

   # 测试健康检查
   curl http://localhost:8000/api/health
   ```

4. **停止服务**
   ```bash
   # 停止并删除容器
   docker-compose down

   # 停止但保留容器
   docker-compose stop
   ```

### 方法二：使用 Docker 命令

1. **构建镜像**
   ```bash
   docker build -t z-image-proxy .
   ```

2. **运行容器**
   ```bash
   # 基本运行
   docker run -d \
     --name z-image-proxy \
     -p 8000:8000 \
     z-image-proxy

   # 运行并配置自动重启
   docker run -d \
     --name z-image-proxy \
     -p 8000:8000 \
     --restart unless-stopped \
     z-image-proxy

   # 运行并设置环境变量
   docker run -d \
     --name z-image-proxy \
     -p 8000:8000 \
     --restart unless-stopped \
     -e PORT=8000 \
     -e LOG_LEVEL=DEBUG \
     z-image-proxy
   ```

3. **管理容器**
   ```bash
   # 查看运行状态
   docker ps

   # 查看日志
   docker logs z-image-proxy

   # 实时查看日志
   docker logs -f z-image-proxy

   # 停止容器
   docker stop z-image-proxy

   # 删除容器
   docker rm z-image-proxy

   # 重新启动已停止的容器
   docker start z-image-proxy
   ```

## ⚙️ 配置选项

### 环境变量

可以通过环境变量自定义服务配置：

```bash
# 在 docker-compose.yml 中配置
environment:
  - PORT=8000                    # 服务端口
  - ZIMAGE_API_HOST=https://zimage.run  # Z-Image API 地址
  - LOG_LEVEL=INFO               # 日志级别 (DEBUG/INFO/WARNING/ERROR)
  - TIMEOUT=30                   # API 请求超时时间（秒）
```

### 端口映射

```bash
# 映射到不同端口
docker run -d \
  --name z-image-proxy \
  -p 8080:8000 \    # 将容器的 8000 端口映射到主机的 8080 端口
  z-image-proxy
```

### 资源限制

```bash
# 限制内存使用
docker run -d \
  --name z-image-proxy \
  --memory=1g \
  --memory-swap=2g \
  -p 8000:8000 \
  z-image-proxy

# 限制 CPU 使用
docker run -d \
  --name z-image-proxy \
  --cpus=1.0 \
  -p 8000:8000 \
  z-image-proxy
```

## 📊 监控和日志

### 查看容器状态

```bash
# 查看所有容器
docker ps -a

# 查看容器详细信息
docker inspect z-image-proxy

# 查看资源使用情况
docker stats z-image-proxy
```

### 日志管理

```bash
# 查看容器日志
docker logs z-image-proxy

# 实时查看日志
docker logs -f z-image-proxy

# 查看最近的日志
docker logs --tail=100 z-image-proxy

# 查看特定时间段的日志
docker logs --since="2023-01-01T00:00:00" z-image-proxy
```

### 健康检查

```bash
# 手动执行健康检查
curl http://localhost:8000/api/health

# 查看容器健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 🔧 生产环境部署

### 使用 Docker Compose 进行生产部署

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  z-image-proxy:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: z-image-proxy-prod
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - LOG_LEVEL=INFO
      - ZIMAGE_API_HOST=https://zimage.run
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - z-image-network
    volumes:
      - ./logs:/app/logs  # 持久化日志存储
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

networks:
  z-image-network:
    driver: bridge
```

部署命令：

```bash
# 使用生产配置部署
docker-compose -f docker-compose.prod.yml up -d

# 查看生产环境状态
docker-compose -f docker-compose.prod.yml ps

# 查看生产环境日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 反向代理配置

#### Nginx 配置示例

```nginx
upstream z_image_proxy {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://z_image_proxy;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### 使用 Docker 运行 Nginx

```bash
# 创建 Nginx 配置目录
mkdir -p nginx/conf.d

# 创建 docker-compose 文件
cat > docker-compose.nginx.yml << EOF
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: z-image-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - z-image-proxy
    restart: unless-stopped

  z-image-proxy:
    build: .
    container_name: z-image-proxy
    environment:
      - PORT=8000
    restart: unless-stopped
EOF

# 启动服务
docker-compose -f docker-compose.nginx.yml up -d
```

## 🔒 安全考虑

### 1. 使用非 Root 用户

Dockerfile 中已配置非 root 用户运行：

```dockerfile
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app
```

### 2. 网络隔离

```bash
# 创建自定义网络
docker network create z-image-network

# 运行容器在隔离网络中
docker run -d \
  --name z-image-proxy \
  --network z-image-network \
  -p 8000:8000 \
  z-image-proxy
```

### 3. 资源限制

```bash
# 设置资源限制
docker run -d \
  --name z-image-proxy \
  --memory=2g \
  --cpus=1.0 \
  --pids-limit=100 \
  -p 8000:8000 \
  z-image-proxy
```

### 4. 只读文件系统

```bash
# 运行时设置只读根文件系统
docker run -d \
  --name z-image-proxy \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/log \
  -p 8000:8000 \
  z-image-proxy
```

## 🚀 性能优化

### 1. 多容器负载均衡

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - z-image-proxy

  z-image-proxy:
    build: .
    deploy:
      replicas: 3  # 运行 3 个容器实例
```

### 2. 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.prod.yml z-image-stack

# 扩展服务
docker service scale z-image-stack_z-image-proxy=3
```

### 3. 缓存策略

```bash
# 构建时使用缓存
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from z-image-proxy:latest \
  -t z-image-proxy .
```

## 🛠️ 故障排除

### 常见问题

#### 1. 容器无法启动

```bash
# 查看容器状态
docker ps -a

# 查看容器日志
docker logs z-image-proxy

# 检查容器内部
docker exec -it z-image-proxy /bin/bash
```

#### 2. 端口冲突

```bash
# 查看端口占用
netstat -tulpn | grep :8000
lsof -i :8000

# 使用不同端口
docker run -d -p 8080:8000 z-image-proxy
```

#### 3. 内存不足

```bash
# 查看内存使用
docker stats

# 增加内存限制
docker run -d --memory=4g z-image-proxy
```

#### 4. 网络连接问题

```bash
# 检查网络连接
docker network ls
docker network inspect z-image_z-image-network

# 测试外部连接
docker exec z-image-proxy ping -c 3 zimage.run
```

### 调试技巧

#### 1. 交互式调试

```bash
# 进入运行中的容器
docker exec -it z-image-proxy /bin/bash

# 以调试模式启动容器
docker run -it --rm z-image-proxy /bin/bash
```

#### 2. 查看容器详情

```bash
# 查看容器配置
docker inspect z-image-proxy

# 查看容器进程
docker exec z-image-proxy ps aux

# 查看容器环境变量
docker exec z-image-proxy env
```

## 📦 备份和恢复

### 备份容器数据

```bash
# 备份容器配置
docker inspect z-image-proxy > container-backup.json

# 导出镜像
docker save z-image-proxy > z-image-proxy.tar

# 导出容器（如果需要）
docker export z-image-proxy > z-image-proxy-container.tar
```

### 恢复容器

```bash
# 加载镜像
docker load < z-image-proxy.tar

# 从备份重建容器
docker run -d \
  --name z-image-proxy \
  -p 8000:8000 \
  z-image-proxy
```

## 🔄 更新和维护

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build --no-cache

# 重启服务
docker-compose up -d

# 验证更新
curl http://localhost:8000/api/health
```

### 定期维护

```bash
# 清理无用镜像
docker image prune -f

# 清理无用容器
docker container prune -f

# 清理系统缓存
docker system prune -f

# 查看磁盘使用
docker system df
```

## 📚 扩展阅读

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Docker 最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Z-Image 官方文档](https://zimage.run/)

## 🆘 获取帮助

如果遇到问题，可以：

1. 查看 [GitHub Issues](https://github.com/xianyu110/z-image/issues)
2. 参考 [Docker 官方文档](https://docs.docker.com/)
3. 在容器内查看应用日志：`docker logs z-image-proxy`
4. 检查网络连接和防火墙设置