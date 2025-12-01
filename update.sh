#!/bin/bash

# Z-Image 优雅更新脚本
# 自动检查、备份、更新和重启服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

echo -e "${PURPLE}🔄 Z-Image 优雅更新工具${NC}"
echo "=================================="

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 检查是否在项目根目录
check_project_root() {
    if [ ! -f "zimage_proxy.py" ] || [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ 请在 Z-Image 项目根目录运行此脚本${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 项目环境检查通过${NC}"
}

# 检查 Git 状态
check_git_status() {
    echo -e "${BLUE}🔍 检查 Git 状态...${NC}"

    # 检查是否有未提交的更改
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo -e "${YELLOW}⚠️  检测到未提交的更改${NC}"

        read -p "是否要提交这些更改? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}📝 自动提交更改...${NC}"
            git add .
            git commit -m "自动备份提交 - $(date)"
            echo -e "${GREEN}✅ 更改已提交${NC}"
        else
            echo -e "${YELLOW}💾 将在备份中包含这些更改${NC}"
        fi
    fi
}

# 备份当前版本
backup_current() {
    echo -e "${BLUE}💾 创建当前版本备份...${NC}"

    # 备份重要文件
    tar -czf "$BACKUP_FILE" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='node_modules' \
        --exclude='backups' \
        --exclude='.DS_Store' \
        --exclude='*.log' \
        . || true

    echo -e "${GREEN}✅ 备份已保存到: $BACKUP_FILE${NC}"
}

# 检查更新
check_updates() {
    echo -e "${BLUE}🔍 检查远程更新...${NC}"

    git fetch origin

    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)

    if [ "$LOCAL" = "$REMOTE" ]; then
        echo -e "${GREEN}✅ 已是最新版本${NC}"
        return 1
    else
        echo -e "${YELLOW}📦 发现新版本${NC}"
        git log --oneline HEAD..origin/main
        return 0
    fi
}

# 执行更新
perform_update() {
    echo -e "${BLUE}🔄 执行更新...${NC}"

    # 拉取最新代码
    git pull origin main

    echo -e "${GREEN}✅ 代码更新完成${NC}"
}

# 更新依赖
update_dependencies() {
    echo -e "${BLUE}📦 更新依赖...${NC}"

    # 检查是否需要更新 Python 依赖
    if [ -f "requirements.txt" ]; then
        echo -e "${CYAN}🐍 更新 Python 依赖...${NC}"
        if command -v python3 &> /dev/null; then
            python3 -m pip install -r requirements.txt --upgrade
        elif command -v python &> /dev/null; then
            python -m pip install -r requirements.txt --upgrade
        fi
    fi

    # 检查前端依赖
    if [ -f "web/package.json" ] && [ -d "web" ]; then
        echo -e "${CYAN}🎨 更新前端依赖...${NC}"
        cd web
        if command -v npm &> /dev/null; then
            npm install
        elif command -v yarn &> /dev/null; then
            yarn install
        fi
        cd ..
    fi

    echo -e "${GREEN}✅ 依赖更新完成${NC}"
}

# 重启服务
restart_services() {
    echo -e "${BLUE}🔄 重启服务...${NC}"

    # 停止现有服务
    if [ -f "start.sh" ]; then
        echo -e "${YELLOW}🛑 停止现有服务...${NC}"
        ./start.sh stop 2>/dev/null || true
    fi

    # Docker 部署
    if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
        echo -e "${CYAN}🐳 更新 Docker 服务...${NC}"
        docker-compose down
        docker-compose build --no-cache
        docker-compose up -d
        echo -e "${GREEN}✅ Docker 服务已重启${NC}"

    # Docker Compose V2
    elif [ -f "docker-compose.yml" ] && command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo -e "${CYAN}🐳 更新 Docker 服务 (V2)...${NC}"
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        echo -e "${GREEN}✅ Docker 服务已重启${NC}"

    # 本地部署
    else
        echo -e "${CYAN}🏠 启动本地服务...${NC}"
        if [ -f "start.sh" ]; then
            ./start.sh start
        else
            echo -e "${YELLOW}⚠️  请手动重启服务${NC}"
        fi
    fi
}

# 健康检查
health_check() {
    echo -e "${BLUE}🏥 执行健康检查...${NC}"

    sleep 5

    # 检查本地服务
    if curl -f http://localhost:8000/api/health &>/dev/null; then
        echo -e "${GREEN}✅ 后端服务运行正常 (端口 8000)${NC}"
    elif curl -f http://localhost:8001/api/health &>/dev/null; then
        echo -e "${GREEN}✅ 后端服务运行正常 (端口 8001)${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务可能未启动或端口不同${NC}"
    fi

    # 检查前端服务
    if curl -f http://localhost:3000 &>/dev/null; then
        echo -e "${GREEN}✅ 前端服务运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务可能未启动${NC}"
    fi
}

# 显示更新摘要
show_summary() {
    echo -e "\n${PURPLE}📊 更新摘要${NC}"
    echo "=================================="
    echo -e "${GREEN}✅ 更新完成${NC}"
    echo -e "${BLUE}📁 备份位置: $BACKUP_FILE${NC}"
    echo -e "${BLUE}🕐 更新时间: $(date)${NC}"

    echo -e "\n${CYAN}🔗 访问地址:${NC}"
    echo "   后端 API: http://localhost:8000 或 http://localhost:8001"
    echo "   前端界面: http://localhost:3000"

    echo -e "\n${CYAN}🛠️  常用命令:${NC}"
    echo "   查看状态: ./start.sh status"
    echo "   停止服务: ./start.sh stop"
    echo "   重启服务: ./start.sh restart"
    echo "   查看日志: tail -f backend.log frontend.log"

    echo -e "\n${YELLOW}💡 如有问题，可以使用备份回滚: tar -xzf $BACKUP_FILE${NC}"
}

# 错误处理
handle_error() {
    echo -e "\n${RED}❌ 更新过程中出现错误${NC}"
    echo -e "${YELLOW}💾 备份文件: $BACKUP_FILE${NC}"
    echo -e "${YELLOW}🔄 可以使用以下命令回滚:${NC}"
    echo -e "   tar -xzf $BACKUP_FILE"

    exit 1
}

# 设置错误处理
trap handle_error ERR

# 主更新流程
main() {
    echo -e "${CYAN}开始优雅更新流程...${NC}\n"

    check_project_root
    check_git_status
    backup_current

    if check_updates; then
        perform_update
        update_dependencies
        restart_services
        health_check
        show_summary
    else
        echo -e "${GREEN}✅ 无需更新，当前已是最新版本${NC}"
        exit 0
    fi
}

# 检查参数
case "${1:-update}" in
    "update")
        main
        ;;
    "check")
        check_project_root
        check_updates || echo -e "${GREEN}✅ 已是最新版本${NC}"
        ;;
    "backup")
        check_project_root
        backup_current
        ;;
    "restore")
        if [ -z "${2:-}" ]; then
            echo -e "${RED}❌ 请指定备份文件${NC}"
            echo "用法: $0 restore <backup_file>"
            exit 1
        fi
        echo -e "${BLUE}🔄 从备份恢复...${NC}"
        tar -xzf "$2"
        echo -e "${GREEN}✅ 恢复完成${NC}"
        ;;
    "help"|"-h"|"--help")
        echo -e "${BLUE}Z-Image 优雅更新工具${NC}"
        echo ""
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  update     执行完整更新流程 (默认)"
        echo "  check      仅检查是否有更新"
        echo "  backup     仅创建备份"
        echo "  restore    从备份恢复"
        echo "  help       显示帮助信息"
        echo ""
        echo "示例:"
        echo "  $0                # 执行完整更新"
        echo "  $0 check          # 检查更新"
        echo "  $0 restore ./backups/backup_20231201_120000.tar.gz  # 恢复备份"
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac