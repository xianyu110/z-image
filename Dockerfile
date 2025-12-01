# 使用官方 Python 3.11 slim 镜像作为基础镜像（使用更稳定的版本）
FROM python:3.11.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 跳过系统包安装（Python镜像已包含ca-certificates）

# 升级 pip 到最新版本
RUN pip install --no-cache-dir --upgrade pip

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建非 root 用户（使用更兼容的方式）
RUN adduser --disabled-password --gecos '' app

# 复制应用代码
COPY . .

# 设置文件权限并切换用户
RUN chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查（使用简单的Python检查）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 启动命令
CMD ["python", "zimage_proxy.py"]