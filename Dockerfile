# 使用官方 Python 3.11 slim 镜像作为基础镜像（使用更稳定的版本）
FROM python:3.11.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    APT_OPTIONS="-o Acquire::Retries=3 -o Acquire::http::Timeout=10 -o Acquire::https::Timeout=10"

# 安装必要的系统依赖（最小化依赖）
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 升级 pip 到最新版本
RUN pip install --no-cache-dir --upgrade pip

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建非 root 用户（使用更兼容的方式）
RUN adduser --disabled-password --gecos '' app

# 复制应用代码并设置权限
COPY --chown=app:app . .

# 设置正确的权限
USER app

# 暴露端口
EXPOSE 8000

# 健康检查（使用简单的Python检查）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 启动命令
CMD ["python", "zimage_proxy.py"]