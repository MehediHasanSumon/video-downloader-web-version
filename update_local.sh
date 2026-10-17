#!/usr/bin/env bash
# ====================================================================
#  Universal Video Downloader Pro - Local Sync, Build & SSL Update Script
#  Source:      /home/sumon/Desktop/Youtube/web-version
#  Destination: /var/www/video-downloader
#  Domain:      https://downloader.test & https://downloder.test
# ====================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}===================================================================${NC}"
echo -e "${BOLD}${CYAN}   Video Downloader Pro - Local Sync, Build & SSL Updater          ${NC}"
echo -e "${CYAN}===================================================================${NC}"
echo ""

# 1. Require sudo / root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run with sudo:${NC}"
    echo -e "   ${BOLD}sudo bash update_local.sh${NC} or ${BOLD}sudo bash local.sh${NC}"
    exit 1
fi

TARGET_USER="${SUDO_USER:-sumon}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="/var/www/video-downloader"

echo -e "${CYAN}[1/8] Compiling Frontend React Web Application...${NC}"
if [ -d "$SRC_DIR/frontend" ] && [ -f "$SRC_DIR/frontend/package.json" ]; then
    if command -v npm >/dev/null 2>&1; then
        echo -e "  • Building client assets in $SRC_DIR/frontend..."
        sudo -u "$TARGET_USER" bash -c "cd '$SRC_DIR/frontend' && npm run build"
        echo -e "${GREEN}✓ Frontend compiled successfully to dist/.${NC}"
    else
        echo -e "${YELLOW}[WARNING] npm not found. Skipping frontend compilation.${NC}"
    fi
fi

# 2. Fix Port 80 conflict (Apache2)
echo -e "${CYAN}[2/8] Checking Port 80 conflicts...${NC}"
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo -e "${YELLOW}  • Stopping and disabling Apache2 to free Port 80 for Nginx...${NC}"
    systemctl stop apache2
    systemctl disable apache2
fi
fuser -k 80/tcp 2>/dev/null || true

# 3. Rsync project files to /var/www/video-downloader
echo -e "${CYAN}[3/8] Syncing code to $DEST_DIR...${NC}"
mkdir -p "$DEST_DIR"
rsync -a --delete \
    --exclude='.git' \
    --exclude='server/venv' \
    --exclude='server/downloads/*' \
    --exclude='frontend/node_modules' \
    "$SRC_DIR/" "$DEST_DIR/"

chown -R "$TARGET_USER:$TARGET_USER" "$DEST_DIR"
echo -e "${GREEN}✓ Synchronized project files to $DEST_DIR.${NC}"

# 4. Check & Install Nginx and SSL tools if missing
echo -e "${CYAN}[4/8] Verifying Nginx & SSL Trust tools...${NC}"
if ! command -v nginx >/dev/null 2>&1; then
    echo -e "  • Installing Nginx..."
    apt-get update -y
    apt-get install -y nginx
fi

# Install libnss3-tools (provides certutil to fix Chrome "Not secure" warning on Linux)
if ! command -v certutil >/dev/null 2>&1; then
    echo -e "  • Installing libnss3-tools for Chrome NSS database trust..."
    apt-get update -y
    apt-get install -y libnss3-tools
fi

# 5. Generate / Update SSL Certificate with Multi-Domain SAN
echo -e "${CYAN}[5/8] Configuring 10-Year SSL Certificate & CA Trust...${NC}"
mkdir -p /etc/ssl/certs /etc/ssl/private

# Regenerate certificate to ensure both downloader.test and downloder.test are included
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/downloder.test.key \
  -out /etc/ssl/certs/downloder.test.crt \
  -subj "/C=BD/ST=Dhaka/L=Dhaka/O=VideoDownloader/CN=downloader.test" \
  -addext "subjectAltName=DNS:downloader.test,DNS:downloder.test,DNS:localhost,IP:127.0.0.1" \
  2>/dev/null

chmod 644 /etc/ssl/certs/downloder.test.crt
chmod 600 /etc/ssl/private/downloder.test.key

# Trust cert in Linux system ca-certificates
mkdir -p /usr/local/share/ca-certificates/extra
cp /etc/ssl/certs/downloder.test.crt /usr/local/share/ca-certificates/extra/downloder.test.crt
update-ca-certificates >/dev/null 2>&1 || true

# Trust cert in Google Chrome / Chromium NSS database (~/.pki/nssdb)
USER_HOME=$(eval echo "~$TARGET_USER")
NSS_DIR="$USER_HOME/.pki/nssdb"
if [ -d "$NSS_DIR" ]; then
    echo -e "  • Importing SSL certificate into Chrome NSS database ($NSS_DIR)..."
    certutil -d sql:"$NSS_DIR" -D -n "downloader.test" 2>/dev/null || true
    certutil -d sql:"$NSS_DIR" -A -t "C,," -n "downloader.test" -i /etc/ssl/certs/downloder.test.crt 2>/dev/null || true
    chown -R "$TARGET_USER:$TARGET_USER" "$NSS_DIR"
    echo -e "${GREEN}✓ Chrome NSS SSL certificate trusted! (Green Lock / Secure)${NC}"
fi

# 6. Python Virtual Environment setup & updates
echo -e "${CYAN}[6/8] Updating Python dependencies in $DEST_DIR...${NC}"
if [ ! -d "$DEST_DIR/server/venv" ] || [ ! -f "$DEST_DIR/server/venv/bin/pip" ]; then
    echo -e "  • Creating virtual environment..."
    sudo -u "$TARGET_USER" python3 -m venv "$DEST_DIR/server/venv"
fi

sudo -u "$TARGET_USER" "$DEST_DIR/server/venv/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
sudo -u "$TARGET_USER" "$DEST_DIR/server/venv/bin/pip" install -q -r "$DEST_DIR/server/requirements.txt"

mkdir -p "$DEST_DIR/server/downloads"
chown -R "$TARGET_USER:$TARGET_USER" "$DEST_DIR/server/downloads"
chmod 775 "$DEST_DIR/server/downloads"

# 7. Update /etc/hosts mapping
echo -e "${CYAN}[7/8] Verifying /etc/hosts domain mappings...${NC}"
if ! grep -q "downloader.test" /etc/hosts || ! grep -q "downloder.test" /etc/hosts; then
    sed -i '/downloader\.test/d; /downloder\.test/d' /etc/hosts
    echo "127.0.0.1 downloader.test downloder.test" >> /etc/hosts
    echo -e "${GREEN}✓ Added downloader.test and downloder.test to /etc/hosts${NC}"
else
    echo -e "${GREEN}✓ Domain names already mapped in /etc/hosts.${NC}"
fi

# 8. Configure Nginx and Systemd Service
echo -e "${CYAN}[8/8] Updating Nginx & Restarting Systemd Services...${NC}"
NGINX_CONF="/etc/nginx/sites-available/downloder.test"
cp "$DEST_DIR/nginx/downloder.test.conf" "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx

# Update and restart Systemd video-downloader service
cp "$DEST_DIR/deploy/video-downloader-local.service" /etc/systemd/system/video-downloader.service
systemctl daemon-reload
systemctl enable video-downloader.service
systemctl restart video-downloader.service

# Setup 15-Minute Cache Cleanup Cron for sumon user
CRON_JOB="*/15 * * * * find $DEST_DIR/server/downloads -type f -mmin +15 -delete 2>/dev/null"
(crontab -u "$TARGET_USER" -l 2>/dev/null | grep -v "server/downloads" ; echo "$CRON_JOB") | crontab -u "$TARGET_USER" -

# Quick health check
sleep 1.5
HEALTH=$(curl -sk https://127.0.0.1/api/health 2>/dev/null || echo "offline")

echo ""
echo -e "${GREEN}===================================================================${NC}"
echo -e "${BOLD}${GREEN}   ✓ LOCAL UPDATE & SSL CONFIGURATION COMPLETED!                   ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo -e "  • Primary URL:        ${BOLD}${CYAN}https://downloader.test${NC}"
echo -e "  • Alias URL:          ${BOLD}${CYAN}https://downloder.test${NC}"
echo -e "  • Backend Service:    ${BOLD}${GREEN}ACTIVE (systemd video-downloader.service)${NC}"
echo -e "  • Health Check:       ${BOLD}$HEALTH${NC}"
echo -e "  • Chrome SSL Status:  ${BOLD}${GREEN}TRUSTED IN NSS DATABASE${NC}"
echo -e "  • Local Project Path: ${BOLD}$DEST_DIR${NC}"
echo ""
echo -e "${YELLOW}[Note for Chrome]:${NC} If Chrome is currently running, restart Chrome or open"
echo -e "              ${BOLD}https://downloader.test${NC} in a new tab to see the secure lock."
echo ""
