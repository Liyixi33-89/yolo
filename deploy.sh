#!/bin/bash

# YOLO11 项目自动部署脚本
# 用法: ./deploy.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "🚀 YOLO11 多功能视觉识别系统 - 自动部署"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录（修改为实际路径）
PROJECT_DIR="$HOME/projects/yolo"

# 进入项目目录
cd "$PROJECT_DIR"

echo -e "${YELLOW}📥 步骤 1/5: 拉取最新代码...${NC}"
git fetch origin
git pull origin main
echo -e "${GREEN}✓ 代码更新完成${NC}"

echo -e "${YELLOW}🐍 步骤 2/5: 更新 Python 依赖...${NC}"
source venv/bin/activate
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Python 依赖更新完成${NC}"

echo -e "${YELLOW}⚛️ 步骤 3/5: 构建前端...${NC}"
cd frontend
npm install --silent
npm run build
# 构建完成后删除 node_modules 以节省磁盘空间
echo -e "${YELLOW}🧹 清理前端依赖...${NC}"
rm -rf node_modules
cd ..
echo -e "${GREEN}✓ 前端构建完成，已清理 node_modules${NC}"

echo -e "${YELLOW}🔄 步骤 4/5: 重启后端服务...${NC}"
pm2 restart yolo-backend || pm2 start ecosystem.config.js
echo -e "${GREEN}✓ 后端服务重启完成${NC}"

echo -e "${YELLOW}📋 步骤 5/5: 检查服务状态...${NC}"
pm2 status
echo ""

echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo "后端日志: pm2 logs yolo-backend"
echo "=========================================="
