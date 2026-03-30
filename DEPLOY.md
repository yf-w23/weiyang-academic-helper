# 部署指南 - 未央书院学业助手

## 方式一：Docker Compose 部署（推荐）

### 1. 准备云服务器

购买云服务器（推荐）：
- **阿里云 ECS**: https://www.aliyun.com/product/ecs
- **腾讯云 CVM**: https://cloud.tencent.com/product/cvm
- **华为云 ECS**: https://www.huaweicloud.com/product/ecs.html

最低配置要求：
- CPU: 1 核
- 内存: 2 GB
- 硬盘: 20 GB
- 带宽: 1 Mbps
- 系统: Ubuntu 20.04/22.04 LTS

### 2. 服务器初始化

```bash
# 连接到服务器（Windows 用 PowerShell，Mac/Linux 用 Terminal）
ssh root@你的服务器IP

# 更新系统
apt update && apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
apt install docker-compose -y

# 启动 Docker
systemctl start docker
systemctl enable docker

# 检查安装
docker --version
docker-compose --version
```

### 3. 下载项目代码

```bash
# 安装 git
apt install git -y

# 克隆项目（替换为你的仓库地址）
cd /opt
git clone https://github.com/yf-w23/weiyang-academic-helper.git
cd weiyang-academic-helper
```

### 4. 配置环境变量

```bash
# 复制生产环境配置
cp .env.production .env

# 编辑配置文件
nano .env
```

填入你的真实 API Key：
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PADDLEOCR_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

按 `Ctrl+O` 保存，`Ctrl+X` 退出。

### 5. 启动服务

```bash
# 构建并启动容器
docker-compose up -d --build

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 6. 访问网站

浏览器访问：`http://你的服务器IP`

---

## 方式二：手动部署（分别部署前后端）

### 后端部署

```bash
# 1. 安装 Python 依赖
apt install python3-pip python3-venv -y

# 2. 创建虚拟环境
cd /opt/weiyang-academic-helper
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -e .

# 4. 配置环境变量
export DEEPSEEK_API_KEY=your_key
export PADDLEOCR_ACCESS_TOKEN=your_token

# 5. 启动后端
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端部署

```bash
# 1. 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 2. 构建前端
cd frontend/react-app
npm install
npm run build

# 3. 安装 Nginx
apt install nginx -y

# 4. 复制构建文件
cp -r dist/* /var/www/html/

# 5. 配置 Nginx
cp nginx.conf /etc/nginx/sites-available/default

# 6. 重启 Nginx
systemctl restart nginx
```

---

## 方式三：使用云平台一键部署

### 阿里云 Serverless（函数计算 FC）

适合轻量级应用，按量付费：

1. 登录阿里云控制台
2. 进入「函数计算 FC」
3. 创建服务 → 创建函数
4. 选择「自定义容器」
5. 上传你的 Docker 镜像

### 腾讯云 CloudBase（云开发）

适合全栈应用：

1. 登录腾讯云 CloudBase
2. 创建环境
3. 选择「托管服务」
4. 上传代码或关联 GitHub 仓库

---

## 常用运维命令

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
git pull
docker-compose up -d --build

# 查看资源占用
docker stats
```

---

## 配置 HTTPS（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx -y

# 申请证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

---

## 域名配置

1. 购买域名（阿里云/腾讯云/GoDaddy）
2. 添加 A 记录指向服务器 IP
3. 等待 DNS 生效（通常 10 分钟）
4. 配置 Nginx 使用域名

---

## 故障排查

### 1. 端口被占用

```bash
# 查看 80 端口占用
netstat -tulpn | grep :80

# 停止占用进程
kill -9 <PID>
```

### 2. 后端无法启动

```bash
# 检查环境变量
docker-compose exec backend env

# 手动测试后端
docker-compose exec backend python -c "from backend.main import app; print('OK')"
```

### 3. 前端无法访问

```bash
# 检查 Nginx 配置
nginx -t

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 4. 防火墙问题

```bash
# 开放 80 端口
ufw allow 80
ufw allow 443
ufw enable
```

---

## 性能优化

1. **启用 Gzip 压缩**: Nginx 配置中已启用
2. **静态文件缓存**: Nginx 配置中已设置 1 年缓存
3. **数据库连接池**: FastAPI 默认支持
4. **CDN 加速**: 可将静态资源放到 CDN

---

## 监控告警

推荐使用：
- **Prometheus + Grafana**: 专业监控
- **Uptime Kuma**: 简单监控（Docker 一键部署）

```bash
# 部署 Uptime Kuma
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

---

## 备份策略

定期备份重要数据：

```bash
# 创建备份脚本
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/$DATE"
mkdir -p $BACKUP_DIR

# 备份代码
cd /opt/weiyang-academic-helper && git bundle create $BACKUP_DIR/code.bundle --all

# 备份配置
cp .env $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /opt/backup.sh

# 添加到定时任务（每天凌晨 2 点备份）
echo "0 2 * * * /opt/backup.sh" | crontab -
```

---

## 联系支持

遇到问题？
1. 查看日志：`docker-compose logs`
2. 检查 GitHub Issues
3. 联系云服务提供商客服
