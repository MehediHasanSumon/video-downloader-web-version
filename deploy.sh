#!/usr/bin/env bash
# ====================================================================
#  Universal Video Downloader Pro - 1-Click Production VPS Deployer
#  Supported OS: Ubuntu 20.04/22.04/24.04, Debian 11/12
# ====================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}===================================================================${NC}"
echo -e "${BOLD}   Video Downloader Pro - 1-Click Production VPS Setup             ${NC}"
echo -e "${CYAN}===================================================================${NC}"
echo ""

# 1. Check Root / Sudo privileges
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo or as root: sudo bash deploy.sh${NC}"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 2. System updates & package installation
echo -e "${CYAN}[1/7] Installing system dependencies (Python 3, FFmpeg, Nginx, Curl)...${NC}"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip ffmpeg nginx curl git ufw

# 3. Check or install Node.js (for frontend build)
if ! command -v node >/dev/null 2>&1; then
    echo -e "${CYAN}[2/7] Installing Node.js LTS for frontend compilation...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# 4. Build Frontend React bundle
echo -e "${CYAN}[3/7] Compiling Frontend React Web Application...${NC}"
if [ -d "$SCRIPT_DIR/frontend" ]; then
    (
        cd "$SCRIPT_DIR/frontend"
        npm install
        npm run build
    )
fi

# 5. Setup Python Virtual Environment for Server
echo -e "${CYAN}[4/7] Setting up Python virtual environment and dependencies...${NC}"
if [ ! -d "$SCRIPT_DIR/server/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/server/venv"
fi
"$SCRIPT_DIR/server/venv/bin/pip" install --upgrade pip
"$SCRIPT_DIR/server/venv/bin/pip" install -r "$SCRIPT_DIR/server/requirements.txt"

# Create downloads folder
mkdir -p "$SCRIPT_DIR/server/downloads"
chmod -R 775 "$SCRIPT_DIR/server/downloads"

# 6. Configure Systemd Service
echo -e "${CYAN}[5/7] Configuring Systemd Background Service...${NC}"
SERVICE_FILE="/etc/systemd/system/video-downloader.service"
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Universal Video Downloader Pro - Production Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONUNBUFFERED=1
Environment=HOST=127.0.0.1
Environment=PORT=5000
Environment=FILE_RETENTION_SECONDS=900
EnvironmentFile=-$SCRIPT_DIR/.env
ExecStart=$SCRIPT_DIR/server/venv/bin/python3 server/main.py --host 127.0.0.1 --port 5000 --no-browser
Restart=always
RestartSec=5s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable video-downloader.service
systemctl restart video-downloader.service

# 7. Configure Nginx Reverse Proxy
echo -e "${CYAN}[6/7] Configuring Nginx Reverse Proxy...${NC}"
NGINX_CONF="/etc/nginx/sites-available/video-downloader"
cp "$SCRIPT_DIR/nginx/video-downloader.conf" "$NGINX_CONF"

# Enable site in Nginx
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
# Remove default nginx welcome page if active
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default
fi

nginx -t
systemctl reload nginx

# 8. Configure Firewall (UFW)
echo -e "${CYAN}[7/7] Configuring UFW Firewall...${NC}"
if command -v ufw >/dev/null 2>&1; then
    ufw allow 22/tcp || true
    ufw allow 80/tcp || true
    ufw allow 443/tcp || true
    echo "y" | ufw enable || true
fi

PUBLIC_IP=$(curl -s https://api.ipify.org || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}===================================================================${NC}"
echo -e "${BOLD}       PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!                ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo ""
echo -e "  ${BOLD}➜ Website URL:${NC}       ${CYAN}http://${PUBLIC_IP}${NC}"
echo -e "  ${BOLD}➜ Service Status:${NC}    systemctl status video-downloader"
echo -e "  ${BOLD}➜ Service Logs:${NC}      journalctl -u video-downloader -f"
echo ""
echo -e "${YELLOW}[Optional SSL/HTTPS]:${NC}"
echo -e "  Point your domain to ${PUBLIC_IP}, then run:"
echo -e "  ${BOLD}sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx${NC}"
echo ""
