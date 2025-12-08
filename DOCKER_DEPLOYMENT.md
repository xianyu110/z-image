# Docker 部署指南

## 快速开始

### 1. 使用 Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/xianyu110/z-image.git
cd z-image

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 2. 使用 Docker 命令

```bash
# 构建镜像
docker build -t z-image .

# 运行容器
docker run -d \
  --name z-image \
  -p 8000:8000 \
  -e ZIMAGE_API_HOST=https://zimage.run \
  -e ENABLE_KEEP_ALIVE=true \
  --restart unless-stopped \
  z-image
```

## 访问服务

- **前端界面**: http://localhost:8000
- **API 健康检查**: http://localhost:8000/health
- **API 端点**: http://localhost:8000/v1/chat/completions

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| PORT | 8000 | 服务端口 |
| PYTHONUNBUFFERED | 1 | Python 输出缓冲 |
| ZIMAGE_API_HOST | https://zimage.run | Z-Image API 地址 |
| ENABLE_KEEP_ALIVE | true | 启用防休眠功能 |
| DEBUG | false | 调试模式 |

## 生产环境部署

### 1. 创建 Docker 网络

```bash
docker network create z-image-prod
```

### 2. 运行容器

```bash
docker run -d \
  --name z-image-prod \
  --network z-image-prod \
  -p 8000:8000 \
  -e PORT=8000 \
  -e ZIMAGE_API_HOST=https://zimage.run \
  -e ENABLE_KEEP_ALIVE=true \
  -v /data/z-image/logs:/app/logs \
  --restart always \
  z-image:latest
```

### 3. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 云平台部署

### Docker Hub

```bash
# 登录 Docker Hub
docker login

# 标记镜像
docker tag z-image:latest yourusername/z-image:latest

# 推送到 Docker Hub
docker push yourusername/z-image:latest
```

### 云服务器部署

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 部署服务
git clone https://github.com/xianyu110/z-image.git
cd z-image
docker-compose up -d

# 设置开机自启
sudo systemctl enable docker
```

## 监控和维护

### 查看日志

```bash
# 查看容器日志
docker logs z-image

# 实���跟踪日志
docker logs -f z-image

# 使用 docker-compose
docker-compose logs -f z-image
```

### 健康检查

```bash
# 手动健康检查
curl http://localhost:8000/health

# 检查容器状态
docker inspect z-image | grep -A 10 "Health"
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并运行
docker-compose down
docker-compose up -d --build
```

## 性能优化

### 1. 多实例部署

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  z-image:
    build: .
    environment:
      - PORT=8000
    scale: 3  # 运行3个实例

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### 2. 使用 Redis 缓存（可选）

```yaml
services:
  z-image:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:alpine
    restart: unless-stopped
```

## 故障排除

### 问题1：容器无法启动

```bash
# 检查日志
docker logs z-image

# 检查端口占用
netstat -tlnp | grep 8000

# 强制停止并删除
docker rm -f z-image
```

### 问题2：API 连接失败

- 检查 `ZIMAGE_API_HOST` 环境变量
- 确认网络连接正常
- 查看容器日志中的错误信息

### 问题3：内存不足

```bash
# 限制内存使用
docker run -d \
  --name z-image \
  --memory="1g" \
  --cpus="0.5" \
  z-image
```

## 安全建议

1. **使用非 root 用户运行**（已在 Dockerfile 中配置）
2. **定期更新基础镜像**
3. **限制资源使用**
4. **配置防火墙规则**
5. **使用 HTTPS**（配合 Nginx）

## 备份和恢复

```bash
# 备份数据（如果有）
docker cp z-image:/app/data ./backup/

# 恢复数据
docker cp ./backup/ z-image:/app/data/
```

## 相关命令速查

```bash
# 构建镜像
docker build -t z-image .

# 运行容器
docker run -d -p 8000:8000 z-image

# 查看容器
docker ps

# 停止容器
docker stop z-image

# 删除容器
docker rm z-image

# 删除镜像
docker rmi z-image

# 清理所有资源
docker system prune -a
```

## 项目结构

```
z-image/
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
├── requirements.txt         # Python 依赖
├── zimage_proxy_unified.py # 主服务文件（前后端一体）
├── api/                    # API 相关文件
├── web/                    # 前端文件
│   ├── index.html
│   ├── script.js
│   └── styles.css
└── README.md              # 项目说明
```