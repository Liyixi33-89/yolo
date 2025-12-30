# 🚀 YOLO11 项目服务器部署指南

## 一、SSH 密钥配置（本地 → 服务器）

### 1.1 查看本地公钥

你已经有 SSH 密钥，公钥内容为：
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFOG2NqHvjeLCpnM24I479C7cRu8zzfMDXOa2QzZvfmo liyixi33-89@github.com
```

### 1.2 将公钥添加到服务器

**方法一：使用 ssh-copy-id（推荐，Linux/Mac）**
```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@your_server_ip
```

**方法二：手动添加（Windows 推荐）**

1. 复制本地公钥内容：
```powershell
# Windows PowerShell
type $env:USERPROFILE\.ssh\id_ed25519.pub | clip
```

2. 登录服务器（首次需要密码）：
```powershell
ssh username@your_server_ip
```

3. 在服务器上执行：
```bash
# 创建 .ssh 目录（如果不存在）
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 将公钥添加到 authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFOG2NqHvjeLCpnM24I479C7cRu8zzfMDXOa2QzZvfmo liyixi33-89@github.com" >> ~/.ssh/authorized_keys

# 设置权限
chmod 600 ~/.ssh/authorized_keys
```

### 1.3 配置 SSH Config（可选，简化连接）

在本地创建/编辑 `~/.ssh/config` 文件：
```powershell
# Windows 路径: C:\Users\v_liyixili\.ssh\config
```

添加内容：
```
Host yolo-server
    HostName your_server_ip
    User username
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

之后可以直接使用：
```powershell
ssh yolo-server
```

### 1.4 测试连接
```powershell
ssh username@your_server_ip
# 或使用别名
ssh yolo-server
```

---

## 二、服务器环境配置

### 2.1 安装必要软件

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Git
sudo apt install -y git

# 安装 Nginx（用于反向代理）
sudo apt install -y nginx

# 安装 PM2（Node.js 进程管理）
sudo npm install -g pm2
```

### 2.2 配置 Git SSH（服务器 → GitHub）

在服务器上生成 SSH 密钥：
```bash
# 生成新的 SSH 密钥
ssh-keygen -t ed25519 -C "server@yolo-project"

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

将公钥添加到 GitHub：
1. 登录 GitHub → Settings → SSH and GPG keys → New SSH key
2. 粘贴服务器的公钥内容
3. 保存

测试连接：
```bash
ssh -T git@github.com
# 应显示: Hi Liyixi33-89! You've successfully authenticated...
```

---

## 三、拉取代码并部署

### 3.1 克隆项目
```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆代码
git clone git@github.com:Liyixi33-89/yolo.git
cd yolo
```

### 3.2 部署后端（Python FastAPI）

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 测试运行
python api_server.py
```

### 3.3 部署前端（React）

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建产物在 dist 目录
```

---

## 四、使用 PM2 管理进程

### 4.1 创建 PM2 配置文件

在项目根目录创建 `ecosystem.config.js`：
```javascript
module.exports = {
  apps: [
    {
      name: 'yolo-backend',
      script: 'api_server.py',
      interpreter: './venv/bin/python',
      cwd: '/home/username/projects/yolo',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
```

### 4.2 启动服务
```bash
# 启动后端
pm2 start ecosystem.config.js

# 查看状态
pm2 status

# 查看日志
pm2 logs yolo-backend

# 设置开机自启
pm2 startup
pm2 save
```

---

## 五、Nginx 反向代理配置

### 5.1 创建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/yolo
```

添加内容：
```nginx
server {
    listen 80;
    server_name your_domain.com;  # 或服务器 IP

    # 前端静态文件
    location / {
        root /home/username/projects/yolo/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        
        # 增加请求体大小限制（用于图片上传）
        client_max_body_size 50M;
    }
}
```

### 5.2 启用配置
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/yolo /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 六、自动化部署脚本

### 6.1 创建部署脚本

在服务器项目目录创建 `deploy.sh`：
```bash
#!/bin/bash

echo "🚀 开始部署 YOLO11 项目..."

# 进入项目目录
cd ~/projects/yolo

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 更新后端依赖
echo "🐍 更新 Python 依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 更新前端
echo "⚛️ 构建前端..."
cd frontend
npm install
npm run build
cd ..

# 重启服务
echo "🔄 重启服务..."
pm2 restart yolo-backend

echo "✅ 部署完成！"
```

### 6.2 设置执行权限
```bash
chmod +x deploy.sh
```

### 6.3 使用
```bash
./deploy.sh
```

---

## 七、常用命令速查

### 本地操作
```powershell
# 连接服务器
ssh yolo-server

# 推送代码到 GitHub
git add .
git commit -m "update"
git push origin main
```

### 服务器操作
```bash
# 拉取最新代码
git pull origin main

# 查看后端日志
pm2 logs yolo-backend

# 重启后端
pm2 restart yolo-backend

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/error.log

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 八、SSL 证书配置（可选）

使用 Let's Encrypt 免费证书：
```bash
# 安装 certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 九、防火墙配置

```bash
# 允许 SSH
sudo ufw allow 22

# 允许 HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 🔧 故障排查

### 问题1：SSH 连接被拒绝
```bash
# 检查 SSH 服务状态
sudo systemctl status sshd

# 检查防火墙
sudo ufw status
```

### 问题2：后端启动失败
```bash
# 查看 PM2 日志
pm2 logs yolo-backend --lines 100

# 手动测试
source venv/bin/activate
python api_server.py
```

### 问题3：前端无法访问 API
- 检查 Nginx 配置中的代理路径
- 确保后端服务正在运行
- 检查防火墙端口

---

## 📝 快速部署流程总结

1. **本地**：推送代码到 GitHub
   ```powershell
   git add . && git commit -m "update" && git push
   ```

2. **服务器**：执行部署脚本
   ```bash
   ssh yolo-server
   cd ~/projects/yolo && ./deploy.sh
   ```

3. **访问**：打开浏览器访问 `http://your_server_ip`
