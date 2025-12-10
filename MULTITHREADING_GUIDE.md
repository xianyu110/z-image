# Docker容器多线程配置指南

## 概述

本指南介绍了如何配置和优化Docker容器以支持多线程操作，解决 `RuntimeError: can't start new thread` 问题。

## 配置选项

### 1. 最小工作配置 (推荐用于构建问题)

使用 `docker-compose.minimal.yml`：

```bash
docker-compose -f docker-compose.minimal.yml up --build
```

**特性：**
- 使用最简化的Dockerfile避免构建问题
- 启用多线程支持
- 移除所有可能导致失败的配置
- 最小依赖和复杂度

### 2. 简化兼容配置 (推荐用于老版本Docker)

使用 `docker-compose.simple-compatible.yml`：

```bash
docker-compose -f docker-compose.simple-compatible.yml up --build
```

**特性：**
- 兼容Docker Compose所有版本
- 启用多线程支持
- 最小配置复杂度
- 适用于生产环境

### 3. 标准配置 (推荐用于一般使用)

使用 `docker-compose.fixed.yml`：

```bash
docker-compose -f docker-compose.fixed.yml up --build
```

**特性：**
- 启用多线程支持
- 增强的系统限制配置
- 适用于较新版本的Docker Compose

### 4. 高性能配置 (用于高并发需求)

使用 `docker-compose.performance.yml`：

```bash
docker-compose -f docker-compose.performance.yml up --build
```

**特性：**
- 更高的资源限制 (CPU: 4.0, Memory: 2G)
- 多进程支持 (Flask processes: 2)
- 增强的线程数限制
- 适用于高并发场景

## 配置参数说明

### Docker Compose配置

| 参数 | 标准配置 | 高性能配置 | 说明 |
|------|----------|------------|------|
| `cpus` | 2.0 | 4.0 | CPU核心数限制 |
| `memory` | 1G | 2G | 内存限制 |
| `pids` | 1000 | 2000 | 进程/线程数限制 |
| `nproc` | 65535 | 131072 | 最大进程数 |
| `FLASK_PROCESSES` | 1 | 2 | Flask工作进程数 |
| `OMP_NUM_THREADS` | 2 | 4 | OpenMP线程数 |

### 环境变量

```yaml
environment:
  - FLASK_THREADED=true      # 启用Flask多线程
  - FLASK_PROCESSES=1        # Flask进程数
  - ENABLE_KEEP_ALIVE=true   # 启用keep-alive
  - OMP_NUM_THREADS=2        # 计算库线程数
  - MKL_NUM_THREADS=2        # Intel MKL线程数
```

## 使用工具

### 1. 资源监控

```bash
# 监控标准配置容器
./scripts/monitor-resources.sh z-image-fixed

# 监控高性能配置容器
./scripts/monitor-resources.sh z-image-high-performance

# 自定义监控间隔
./scripts/monitor-resources.sh z-image-fixed 2
```

**监控内容包括：**
- CPU和内存使用情况
- 线程和进程信息
- 文件描述符限制
- 系统负载

### 2. 多线程测试

```bash
# 运行多线程功能测试
python3 scripts/test-multithreading.py
```

**测试项目：**
- 线程创建能力测试
- 并发请求测试
- 响应时间统计
- 线程使用情况分析

## 故障排除

### 1. 线程创建失败

如果仍然遇到 `can't start new thread` 错误：

1. **检查主机资源限制**：
   ```bash
   # 查看系统线程限制
   cat /proc/sys/kernel/threads-max

   # 查看用户进程限制
   ulimit -u
   ```

2. **降低并发级别**：
   ```yaml
   environment:
     - FLASK_THREADED=false   # 禁用多线程
     - FLASK_PROCESSES=1      # 使用单进程
   ```

3. **增加资源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         pids: 5000          # 增加进程/线程限制
   ```

### 2. 内存不足

如果遇到内存相关错误：

1. **增加内存限制**：
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G          # 增加内存
   ```

2. **优化内存使用**：
   ```yaml
   environment:
     - MALLOC_ARENA_MAX=1    # 减少内存分配器arena数量
   ```

### 3. 性能问题

如果性能不佳：

1. **监控资源使用**：
   ```bash
   docker stats z-image-fixed
   ```

2. **调整线程数**：
   ```yaml
   environment:
     - FLASK_PROCESSES=2     # 增加进程数
     - OMP_NUM_THREADS=4     # 增加计算线程数
   ```

## 性能调优建议

### 1. 根据主机规格调整

- **2核CPU**: 使用标准配置
- **4核CPU**: 使用高性能配置
- **8核CPU+**: 可以进一步增加资源限制

### 2. 根据负载类型调整

- **I/O密集型**: 增加线程数，减少进程数
- **CPU密集型**: 增加进程数，适当增加线程数
- **混合负载**: 平衡进程数和线程数

### 3. 内存优化

```yaml
environment:
  - MALLOC_ARENA_MAX=2        # 控制内存分配器
  - PYTHONOPTIMIZE=2         # Python优化级别
```

## 安全注意事项

1. **避免特权模式**: 除非必要，不要使用 `privileged: true`
2. **资源限制**: 设置合理的资源限制防止资源耗尽
3. **监控**: 定期监控容器资源使用情况
4. **更新**: 保持Docker和基础镜像的更新

## 常见问题

### Q: 为什么需要这么多配置？
A: Docker容器默认有较低的线程限制，这些配置确保容器有足够的资源来创建和管理线程。

### Q: 多线程一定会提高性能吗？
A: 不一定。对于I/O密集型任务，多线程可以提高性能；但对于CPU密集型任务，过多的线程可能导致上下文切换开销。

### Q: 如何知道我的容器是否真的使用了多线程？
A: 使用提供的测试脚本或监控工具来验证线程使用情况。

### Q: 可以在生产环境使用高性能配置吗？
A: 可以，但建议先在测试环境验证，并根据实际负载调整参数。