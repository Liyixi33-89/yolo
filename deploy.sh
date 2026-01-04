#!/bin/bash

# ============================================================
# YOLO 视觉识别项目 - 自动部署脚本
# 用法: ./deploy.sh [选项]
# 选项:
#   --skip-build    跳过前端构建
#   --skip-pull     跳过代码拉取
#   --check-only    仅检查接口状态
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
VENV_DIR="${PROJECT_DIR}/venv"

# API 地址
API_BASE="http://localhost:8000"

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

# 检查单个接口
check_api() {
    local name=$1
    local url=$2
    local response
    local http_code

    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        log_success "$name: 正常 (HTTP $http_code)"
        # 解析并显示关键信息
        if echo "$body" | grep -q "configured"; then
            configured=$(echo "$body" | grep -o '"configured":[^,}]*' | cut -d':' -f2)
            if [ "$configured" = "true" ]; then
                echo "         └─ 已配置 ✓"
            else
                echo -e "         └─ ${YELLOW}未配置密钥${NC}"
            fi
        fi
        return 0
    else
        log_error "$name: 异常 (HTTP $http_code)"
        return 1
    fi
}

# 等待服务启动（带重试机制）
wait_for_service() {
    local max_attempts=30
    local attempt=1
    local wait_seconds=2
    
    log_info "等待服务启动（最多等待 ${max_attempts} 次，每次 ${wait_seconds} 秒）..."
    
    while [ $attempt -le $max_attempts ]; do
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE}/health" 2>/dev/null)
        
        if [ "$http_code" = "200" ]; then
            log_success "服务已启动！（第 $attempt 次检查）"
            return 0
        fi
        
        echo -ne "\r${BLUE}[INFO]${NC} 等待中... (${attempt}/${max_attempts}) HTTP: ${http_code}"
        sleep $wait_seconds
        ((attempt++))
    done
    
    echo ""
    log_error "服务启动超时（等待了 $((max_attempts * wait_seconds)) 秒）"
    return 1
}

# 检查所有接口
check_all_apis() {
    print_header "接口状态检查"
    
    local failed=0
    
    # 等待服务启动（带重试）
    if ! wait_for_service; then
        log_error "服务未正常启动，请检查日志"
        log_info "查看日志: pm2 logs yolo-backend --lines 50"
        return 1
    fi
    
    echo ""
    
    # 1. 健康检查（此时已确认服务启动）
    log_info "检查服务健康状态..."
    if ! check_api "健康检查" "${API_BASE}/health"; then
        log_error "服务异常，请检查日志"
        return 1
    fi
    
    echo ""
    log_info "检查各平台 API 状态..."
    
    # 2. YOLO 本地检测
    check_api "YOLO 本地检测" "${API_BASE}/api/status" || ((failed++))
    
    # 3. 腾讯云 API
    check_api "腾讯云 API" "${API_BASE}/api/tencent/status" || ((failed++))
    
    # 4. 百度 AI API
    check_api "百度 AI API" "${API_BASE}/api/baidu/status" || ((failed++))
    
    # 5. 车牌识别 API
    check_api "车牌识别 API" "${API_BASE}/api/lpr/status" || ((failed++))
    
    echo ""
    if [ $failed -eq 0 ]; then
        log_success "所有接口检查通过！"
    else
        log_warning "有 $failed 个接口异常，请检查配置"
    fi
    
    return $failed
}

# 拉取代码
pull_code() {
    print_header "拉取最新代码"
    
    cd "$PROJECT_DIR"
    
    log_info "当前分支: $(git branch --show-current)"
    log_info "拉取代码..."
    
    git fetch origin
    git pull origin test
    
    log_success "代码拉取完成"
    log_info "最新提交: $(git log -1 --pretty=format:'%h - %s (%cr)')"
}

# 安装后端依赖
install_backend_deps() {
    print_header "检查后端依赖"
    
    cd "$PROJECT_DIR"
    
    if [ -f "requirements.txt" ]; then
        log_info "安装/更新 Python 依赖..."
        "${VENV_DIR}/bin/pip" install -r requirements.txt -q
        log_success "后端依赖安装完成"
    fi
}

# 构建前端
build_frontend() {
    print_header "构建前端"
    
    cd "$FRONTEND_DIR"
    
    log_info "安装前端依赖..."
    npm install --silent
    
    log_info "构建前端项目..."
    npm run build
    
    # 清理 node_modules 节省空间
    log_info "清理 node_modules..."
    rm -rf node_modules
    
    log_success "前端构建完成"
}

# 停止旧进程并确保端口释放
kill_old_process() {
    log_info "检查端口 8000 占用情况..."
    
    local pid=$(lsof -t -i :8000 2>/dev/null)
    if [ -n "$pid" ]; then
        log_warning "端口 8000 被进程 $pid 占用，正在终止..."
        kill -9 $pid 2>/dev/null || true
        sleep 2
        
        # 再次检查
        pid=$(lsof -t -i :8000 2>/dev/null)
        if [ -n "$pid" ]; then
            log_error "无法释放端口 8000"
            return 1
        fi
        log_success "端口 8000 已释放"
    else
        log_info "端口 8000 未被占用"
    fi
    return 0
}

# 重启服务
restart_service() {
    print_header "重启服务"
    
    cd "$PROJECT_DIR"
    
    # 先停止服务
    log_info "停止当前服务..."
    pm2 stop yolo-backend 2>/dev/null || true
    
    # 等待进程完全停止
    sleep 2
    
    # 确保端口释放
    kill_old_process
    
    # 删除旧进程记录
    log_info "删除旧进程记录..."
    pm2 delete yolo-backend 2>/dev/null || true
    
    # 重新启动服务
    log_info "启动新服务..."
    pm2 start "${VENV_DIR}/bin/python" --name yolo-backend -- api_server.py
    
    # 保存 PM2 配置
    pm2 save --force
    
    log_success "服务已重启"
    
    # 显示服务状态
    log_info "服务状态:"
    pm2 status yolo-backend
}

# 显示日志
show_logs() {
    print_header "最近日志"
    pm2 logs yolo-backend --lines 15 --nostream
}

# 检查密钥配置文件
check_keys_config() {
    print_header "检查密钥配置"
    
    if [ -f "${PROJECT_DIR}/keys.json" ]; then
        log_success "密钥配置文件存在: keys.json"
    else
        log_warning "密钥配置文件不存在！"
        log_info "请复制 keys.json.example 为 keys.json 并填入真实密钥"
        echo ""
        echo "  cp ${PROJECT_DIR}/keys.json.example ${PROJECT_DIR}/keys.json"
        echo "  vim ${PROJECT_DIR}/keys.json"
        echo ""
    fi
}

# 完整部署流程
full_deploy() {
    local skip_build=false
    local skip_pull=false
    
    # 解析参数
    for arg in "$@"; do
        case $arg in
            --skip-build)
                skip_build=true
                ;;
            --skip-pull)
                skip_pull=true
                ;;
        esac
    done
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║         YOLO 视觉识别项目 - 自动部署脚本                 ║"
    echo "║         $(date '+%Y-%m-%d %H:%M:%S')                              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    
    # 1. 检查密钥配置
    check_keys_config
    
    # 2. 拉取代码
    if [ "$skip_pull" = false ]; then
        pull_code
    else
        log_warning "跳过代码拉取"
    fi
    
    # 3. 安装后端依赖
    install_backend_deps
    
    # 4. 构建前端
    if [ "$skip_build" = false ]; then
        build_frontend
    else
        log_warning "跳过前端构建"
    fi
    
    # 5. 重启服务
    restart_service
    
    # 6. 检查接口
    check_all_apis
    
    # 7. 显示日志
    show_logs
    
    echo ""
    print_header "部署完成"
    log_success "项目已成功部署！"
    log_info "访问地址: http://$(hostname -I | awk '{print $1}'):443"
    echo ""
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 解析命令
    case "${1:-}" in
        --check-only)
            check_all_apis
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --skip-build    跳过前端构建"
            echo "  --skip-pull     跳过代码拉取"
            echo "  --check-only    仅检查接口状态"
            echo "  --help, -h      显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                    # 完整部署"
            echo "  $0 --skip-build       # 部署但跳过前端构建"
            echo "  $0 --check-only       # 仅检查接口"
            ;;
        *)
            full_deploy "$@"
            ;;
    esac
}

# 执行主函数
main "$@"
