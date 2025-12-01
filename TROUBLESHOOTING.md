# 故障排除指南

本文档提供了 Z-Image 项目常见问题的解决方案。

## 🐳 Docker 部署问题

### 问题 1: APT 包管理器错误

**错误信息**:
```
E: Problem executing scripts APT::Update::Post-Invoke
E: Sub-process returned an error code: 100
```

**解决方案**:

#### 方法一：使用简化版 Dockerfile
```bash
# 使用 Alpine Linux 版本（推荐）
docker-compose -f docker-compose.simple.yml up -d

# 或使用 Makefile
make build-simple
make run-simple
```

#### 方法二：修复主 Dockerfile
```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
docker-compose build --no-cache
```

#### 方法三：手动安装依赖
```bash
# 创建临时容器
docker run --rm -it python:3.11-slim /bin/bash

# 在容器内手动执行
apt-get update
apt-get install -y gcc
exit
```

### 问题 2: 构建时间过长

**解决方案**:
```bash
# 启用 BuildKit（Docker 18.09+）
export DOCKER_BUILDKIT=1

# 使用缓存构建
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t z-image-proxy .
```

### 问题 3: 端口被占用

**错误信息**:
```
Port 8000 is already allocated
```

**解决方案**:
```bash
# 查看端口占用
lsof -i :8000

# 停止占用端口的容器
docker stop $(docker ps -q --filter "publish=8000")

# 或修改端口映射
docker-compose up -d --scale z-image-proxy=0
sed -i 's/8000:8000/8080:8000/' docker-compose.yml
docker-compose up -d
```

### 问题 4: 内存不足

**错误信息**:
```
Container killed due to memory limit
```

**解决方案**:
```bash
# 增加内存限制
docker-compose up -d --scale z-image-proxy=0
# 编辑 docker-compose.yml，增加内存限制
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## 🚀 API 服务问题

### 问题 1: 连接被拒绝

**错误信息**:
```
Connection refused: localhost:8000
```

**解决方案**:

#### 检查服务状态
```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs z-image-proxy
```

#### 检查端口
```bash
# 检查端口是否监听
netstat -tulpn | grep :8000

# 测试连接
curl http://localhost:8000/api/health
```

#### 重启服务
```bash
# 重启服务
docker-compose restart z-image-proxy

# 完全重建
docker-compose down
docker-compose up -d --build
```

### 问题 2: API 响应慢

**解决方案**:
```bash
# 检查资源使用
docker stats z-image-proxy

# 检查网络延迟
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health
```

### 问题 3: Z-Image API 连接失败

**解决方案**:
```bash
# 检查外部连接
curl -I https://zimage.run

# 设置代理（如果需要）
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# 修改 API 主机
export ZIMAGE_API_HOST=https://alternative-api.com
```

## 🎨 Web 前端问题

### 问题 1: 无法连接到 API

**解决方案**:

#### 检查 API 地址
1. 打开 http://localhost:3000
2. 点击"测试连接"按钮
3. 确认 API 地址正确（默认：http://localhost:8000）

#### 修改 API 地址
```bash
# 在前端界面中修改
# 或编辑 localStorage
localStorage.setItem('apiUrl', 'http://your-api-server:8000')
```

### 问题 2: 前端服务器启动失败

**解决方案**:
```bash
# 检查端口占用
lsof -i :3000

# 使用不同端口
cd web
python server.py 8080
```

### 问题 3: 图片生成失败

**解决方案**:

#### 检查提示词
- 确保提示词不为空
- 避免特殊字符
- 使用英文或简单中文

#### 查看详细日志
```bash
# 查看前端日志
tail -f frontend.log

# 查看后端日志
docker-compose logs -f z-image-proxy
```

## 🖥️ 系统问题

### 问题 1: Python 版本不兼容

**错误信息**:
```
ModuleNotFoundError: No module named 'flask'
```

**解决方案**:
```bash
# 检查 Python 版本
python --version
python3 --version

# 使用正确的版本
python3 -m pip install -r requirements.txt

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 2: 权限问题

**错误信息**:
```
Permission denied
```

**解决方案**:
```bash
# 修改文件权限
chmod +x start.sh
chmod +x web/server.py

# 修改目录权限
chmod -R 755 web/

# 使用 sudo（如果必要）
sudo docker-compose up -d
```

### 问题 3: 磁盘空间不足

**解决方案**:
```bash
# 清理 Docker
docker system prune -a

# 清理日志
sudo journalctl --vacuum-time=7d

# 清理临时文件
rm -rf /tmp/*
```

## 🔍 调试技巧

### 1. 查看容器内部
```bash
# 进入容器
docker exec -it z-image-proxy /bin/bash

# 查看进程
docker exec z-image-proxy ps aux

# 查看环境变量
docker exec z-image-proxy env
```

### 2. 网络调试
```bash
# 测试网络连接
docker exec z-image-proxy ping -c 3 google.com

# 查看 DNS
docker exec z-image-proxy nslookup zimage.run

# 检查端口
docker exec z-image-proxy netstat -tulpn
```

### 3. 日志分析
```bash
# 实时日志
docker-compose logs -f

# 过滤日志
docker-compose logs | grep ERROR

# 日志文件
tail -f /var/log/docker.log
```

## 📞 获取帮助

### 1. 收集信息
在报告问题时，请提供以下信息：

```bash
# 系统信息
uname -a
docker --version
docker-compose --version

# 项目状态
docker-compose ps
docker-compose logs --tail=50

# 错误日志
docker-compose logs z-image-proxy | tail -20
```

### 2. 社区支持
- [GitHub Issues](https://github.com/xianyu110/z-image/issues)
- [Docker 文档](https://docs.docker.com/)
- [Python 文档](https://docs.python.org/)

### 3. 重置环境
如果所有方法都失败，可以重置环境：

```bash
# 完全清理
docker-compose down --rmi all --volumes --remove-orphans
docker system prune -a
docker volume prune

# 重新开始
git pull
docker-compose up -d --build
```

## 🛠️ 预防措施

### 1. 定期维护
```bash
# 每周清理
docker system prune -f

# 监控资源
docker stats

# 备份配置
cp docker-compose.yml docker-compose.yml.backup
```

### 2. 版本管理
```bash
# 锁定版本
docker-compose up -d

# 查看变更
git diff

# 渐进更新
git fetch
git log HEAD..origin/main
```

### 3. 监控设置
```bash
# 设置日志轮转
# 在 docker-compose.yml 中添加
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

如果遇到其他问题，请检查以下常见原因：
1. **网络连接** - 确认能够访问 zimage.run
2. **资源限制** - 检查内存和磁盘空间
3. **权限设置** - 确认 Docker 和文件权限
4. **版本兼容** - 确认 Python 和 Docker 版本