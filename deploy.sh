#!/bin/bash
# ==============================================
# 好风公考情报站 — 一键部署脚本
# 适用：阿里云/腾讯云/华为云 VPS (Ubuntu/Debian)
# ==============================================
set -e

echo "========================================"
echo "  🚀 好风公考情报站 部署脚本"
echo "========================================"

# 1. 安装 Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "📦 安装 Docker..."
    curl -fsSL https://get.docker.com | bash
fi

if ! command -v docker compose &> /dev/null; then
    echo "📦 安装 Docker Compose..."
    apt-get update -y && apt-get install -y docker-compose-plugin
fi

# 2. 下载项目
echo "📥 下载项目..."
if [ ! -d "henan-gwy" ]; then
    git clone https://github.com/your-username/henan-gwy.git
    cd henan-gwy
else
    cd henan-gwy
    git pull
fi

# 3. 构建并启动
echo "🔨 构建 Docker 镜像..."
docker compose build

echo "🚀 启动服务..."
docker compose up -d

# 4. 显示信息
echo ""
echo "========================================"
echo "  ✅ 部署成功！"
echo "========================================"
echo ""
echo "  🌐 本地访问:  http://localhost:5050"
echo "  🌐 服务器IP:  http://$(curl -s ifconfig.me):5050"
echo ""
echo "  📋 管理命令:"
echo "     查看日志:  docker compose logs -f"
echo "     重启服务:  docker compose restart"
echo "     停止服务:  docker compose down"
echo ""
echo "  💡 建议配置 Nginx 反代 + 域名:"
echo "     参考 deploy/nginx.conf"
echo "========================================"
