#!/bin/bash

# Z-Image 快速启动脚本
# 一键启动后端 API 服务器和前端测试界面

set -e

echo "🚀 Z-Image 图片生成服务启动脚本"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ 未找到 Python，请先安装 Python${NC}"
        exit 1
    fi

    echo -e "${GREEN}�� 使用 Python: $(${PYTHON_CMD} --version)${NC}"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用 ($service)${NC}"

        read -p "是否尝试终止占用该端口的进程? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🔄 终止端口 $port 上的进程...${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
            sleep 2
        else
            echo -e "${RED}❌ $service 启动失败${NC}"
            return 1
        fi
    fi
    return 0
}

# 安装依赖
install_dependencies() {
    echo -e "${BLUE}📦 检查依赖...${NC}"

    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ 未找到 requirements.txt${NC}"
        return 1
    fi

    # 检查是否已安装依赖
    if ! $PYTHON_CMD -c "import flask, requests" 2>/dev/null; then
        echo -e "${BLUE}📥 安装 Python 依赖...${NC}"
        $PYTHON_CMD -m pip install -r requirements.txt
    else
        echo -e "${GREEN}✅ 依赖已安装${NC}"
    fi
}

# 启动后端服务器
start_backend() {
    echo -e "${BLUE}🔧 启动后端 API 服务器...${NC}"

    if check_port 8000 "后端 API"; then
        # 在后台启动后端服务器
        nohup $PYTHON_CMD zimage_proxy.py > backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > backend.pid

        # 等待后端启动
        echo -e "${YELLOW}⏳ 等待后端服务器启动...${NC}"
        sleep 3

        # 检查后端是否成功启动
        if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端服务器启动成功 (PID: $BACKEND_PID)${NC}"
            echo -e "${GREEN}🌐 API 地址: http://localhost:8000${NC}"
        else
            echo -e "${RED}❌ 后端服务器启动失败${NC}"
            if [ -f "backend.log" ]; then
                echo -e "${RED}错误日志:${NC}"
                tail -n 10 backend.log
            fi
            return 1
        fi
    else
        return 1
    fi
}

# 启动前端服务器
start_frontend() {
    echo -e "${BLUE}🎨 启动前端测试界面...${NC}"

    if [ ! -d "web" ]; then
        echo -e "${RED}❌ 未找到 web 目录${NC}"
        return 1
    fi

    cd web

    if check_port 3000 "前端界面"; then
        # 在后台启动前端服务器
        nohup $PYTHON_CMD server.py > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > ../frontend.pid

        # 等待前端启动
        echo -e "${YELLOW}⏳ 等待前端服务器启动...${NC}"
        sleep 2

        echo -e "${GREEN}✅ 前端服务器启动成功 (PID: $FRONTEND_PID)${NC}"
        echo -e "${GREEN}🌐 访问地址: http://localhost:3000${NC}"

        # 尝试自动打开浏览器
        if command -v open &> /dev/null; then
            open http://localhost:3000
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:3000
        elif command -v start &> /dev/null; then
            start http://localhost:3000
        else
            echo -e "${BLUE}💡 请手动在浏览器中打开 http://localhost:3000${NC}"
        fi
    else
        cd ..
        return 1
    fi

    cd ..
}

# 显示服务状态
show_status() {
    echo -e "\n${BLUE}📊 服务状态${NC}"
    echo "=================================="

    # 显示后端状态
    if [ -f "backend.pid" ] && kill -0 $(cat backend.pid) 2>/dev/null; then
        echo -e "${GREEN}✅ 后端 API 服务器运行中 (PID: $(cat backend.pid))${NC}"
        echo -e "${GREEN}   地址: http://localhost:8000${NC}"
    else
        echo -e "${RED}❌ 后端 API 服务器未运行${NC}"
    fi

    # 显示前端状态
    if [ -f "frontend.pid" ] && kill -0 $(cat frontend.pid) 2>/dev/null; then
        echo -e "${GREEN}✅ 前端测试界面运行中 (PID: $(cat frontend.pid))${NC}"
        echo -e "${GREEN}   地址: http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ 前端测试界面未运行${NC}"
    fi
}

# 停止服务
stop_services() {
    echo -e "${BLUE}🛑 停止所有服务...${NC}"

    # 停止后端
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${YELLOW}🔄 停止后端服务器 (PID: $BACKEND_PID)...${NC}"
            kill $BACKEND_PID
            sleep 1
        fi
        rm -f backend.pid
    fi

    # 停止前端
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "${YELLOW}🔄 停止前端服务器 (PID: $FRONTEND_PID)...${NC}"
            kill $FRONTEND_PID
            sleep 1
        fi
        rm -f frontend.pid
    fi

    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}用法: $0 [命令]${NC}"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务 (默认)"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    显示服务状态"
    echo "  backend   仅启动后端服务器"
    echo "  frontend  仅启动前端界面"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start     # 启动所有服务"
    echo "  $0 stop      # 停止所有服务"
    echo "  $0 status    # 查看运行状态"
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🔄 正在清理...${NC}"
    stop_services
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    case "${1:-start}" in
        "start")
            echo -e "${BLUE}🚀 启动 Z-Image 服务...${NC}"
            check_python
            install_dependencies
            if start_backend && start_frontend; then
                echo -e "\n${GREEN}🎉 所有服务启动成功！${NC}"
                show_status
                echo -e "\n${BLUE}💡 使用 'Ctrl+C' 停止所有服务${NC}"
                echo -e "${BLUE}📝 查看日志: tail -f backend.log frontend.log${NC}"
                echo -e "${BLUE}🔄 重启服务: $0 restart${NC}"

                # 等待用户中断
                while true; do
                    sleep 1
                done
            else
                echo -e "${RED}❌ 服务启动失败${NC}"
                stop_services
                exit 1
            fi
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            main start
            ;;
        "status")
            show_status
            ;;
        "backend")
            check_python
            install_dependencies
            start_backend
            if [ $? -eq 0 ]; then
                echo -e "\n${GREEN}✅ 后端服务器启动成功！${NC}"
                echo -e "${BLUE}💡 使用 'Ctrl+C' 停止服务器${NC}"
                trap 'kill $(cat backend.pid) 2>/dev/null; rm -f backend.pid; exit 0' SIGINT
                wait $(cat backend.pid) 2>/dev/null
            fi
            ;;
        "frontend")
            check_python
            cd web
            $PYTHON_CMD server.py
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"