#!/bin/bash

# ============================================================
# YOLO 视觉识别项目 - 前端构建脚本
# 用法: ./build_frontend.sh [选项]
# 选项:
#   --no-clean      构建后不清理 node_modules
#   --help, -h      显示帮助信息
# ============================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_DIR="/var/www/yolo"
FRONTEND_DIR="${PROJECT_DIR}/frontend"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "============================================================"
    echo -e "${BLUE}$1${NC}"
    echo "============================================================"
}

# 构建前端
build_frontend() {
    local no_clean=false
    
    # 解析参数
    for arg in "$@"; do
        case $arg in
            --no-clean)
                no_clean=true
                ;;
        esac
    done

    print_header "前端构建开始"
    
    # 检查目录
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "前端目录不存在: $FRONTEND_DIR"
        exit 1
    fi
    
    cd "$FRONTEND_DIR"
    
    log_info "当前目录: $(pwd)"
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install
    
    if [ $? -ne 0 ]; then
        log_error "依赖安装失败"
        exit 1
    fi
    log_success "依赖安装完成"
    
    # 构建项目
    log_info "构建前端项目..."
    npm run build
    
    if [ $? -ne 0 ]; then
        log_error "前端构建失败"
        exit 1
    fi
    log_success "前端构建完成"
    
    # 显示构建产物
    if [ -d "dist" ]; then
        log_info "构建产物目录: ${FRONTEND_DIR}/dist"
        log_info "构建产物大小: $(du -sh dist | cut -f1)"
    fi
    
    # 清理 node_modules
    if [ "$no_clean" = false ]; then
        log_info "清理 node_modules..."
        rm -rf node_modules
        log_success "node_modules 已清理"
    else
        log_warning "跳过 node_modules 清理"
    fi
    
    echo ""
    print_header "前端构建完成"
    log_success "构建时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --no-clean      构建后不清理 node_modules"
    echo "  --help, -h      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 构建前端并清理 node_modules"
    echo "  $0 --no-clean     # 构建前端但保留 node_modules"
    echo ""
}

# 主函数
main() {
    case "${1:-}" in
        --help|-h)
            show_help
            ;;
        *)
            echo ""
            echo "╔══════════════════════════════════════════════════════════╗"
            echo "║         YOLO 视觉识别项目 - 前端构建脚本                 ║"
            echo "║         $(date '+%Y-%m-%d %H:%M:%S')                              ║"
            echo "╚══════════════════════════════════════════════════════════╝"
            build_frontend "$@"
            ;;
    esac
}

# 执行主函数
main "$@"
