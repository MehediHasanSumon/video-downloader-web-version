#!/usr/bin/env bash
# ====================================================================
#  Universal Video Downloader Pro - Local Setup with SSL & Nginx
#  Location: /var/www/video-downloader
#  Domain:   https://downloder.test
# ====================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}===================================================================${NC}"
echo -e "${BOLD}   Video Downloader Pro - Local Setup (/var/www) & SSL              ${NC}"
echo -e "${CYAN}===================================================================${NC}"
echo ""

# 1. Require sudo/root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run with sudo: sudo bash setup_local_ssl.sh${NC}"
    exit 1
fi

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="/var/www/video-downloader"

# 2. Fix Port 80 conflict (Stop & Disable Apache if running)
echo -e "${CYAN}[1/7] Resolving Port 80 conflicts...${NC}"
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo -e "${YELLOW}Stopping and disabling Apache2 to free Port 80 for Nginx...${NC}"
    systemctl stop apache2
    systemctl disable apache2
fi
# Also kill any lingering process on port 80
fuser -k 80/tcp 2>/dev/null || true

# 3. Copy project to /var/www/video-downloader
echo -e "${CYAN}[2/7] Copying project files to $DEST_DIR...${NC}"
mkdir -p "$DEST_DIR"
rsync -a --exclude='.git' --exclude='server/venv' --exclude='server/downloads/*' "$SRC_DIR/" "$DEST_DIR/"
chown -R sumon:sumon "$DEST_DIR"
echo -e "${GREEN}✓ Project copied to $DEST_DIR successfully.${NC}"

# 4. Install Nginx if missing
echo -e "${CYAN}[3/7] Checking Nginx installation...${NC}"
if ! command -v nginx >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing Nginx...${NC}"
    apt-get update -y
    apt-get install -y nginx
fi

# 5. Generate and install SSL Certificates in /etc/ssl
echo -e "${CYAN}[4/7] Generating 10-Year SSL Certificate for downloder.test...${NC}"
mkdir -p /etc/ssl/certs /etc/ssl/private
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/ssl/private/downloder.test.key \
  -out /etc/ssl/certs/downloder.test.crt \
  -subj "/C=BD/ST=Dhaka/L=Dhaka/O=VideoDownloader/CN=downloder.test" \
  -addext "subjectAltName=DNS:downloder.test,DNS:downloader.test,DNS:localhost,IP:127.0.0.1"
chmod 644 /etc/ssl/certs/downloder.test.crt
chmod 600 /etc/ssl/private/downloder.test.key

# Trust cert locally in ca-certificates
mkdir -p /usr/local/share/ca-certificates/extra
cp /etc/ssl/certs/downloder.test.crt /usr/local/share/ca-certificates/extra/downloder.test.crt
update-ca-certificates >/dev/null 2>&1 || true

# 6. Rebuild Python Virtual Environment in /var/www/video-downloader
echo -e "${CYAN}[5/7] Setting up Python virtual environment in $DEST_DIR...${NC}"
if [ ! -d "$DEST_DIR/server/venv" ] || [ ! -f "$DEST_DIR/server/venv/bin/pip" ]; then
    sudo -u sumon python3 -m venv "$DEST_DIR/server/venv"
    sudo -u sumon "$DEST_DIR/server/venv/bin/pip" install --upgrade pip
    sudo -u sumon "$DEST_DIR/server/venv/bin/pip" install -r "$DEST_DIR/server/requirements.txt"
fi
mkdir -p "$DEST_DIR/server/downloads"
chown -R sumon:sumon "$DEST_DIR/server/downloads"
chmod 775 "$DEST_DIR/server/downloads"

# 7. Map downloder.test in /etc/hosts
echo -e "${CYAN}[6/7] Updating /etc/hosts...${NC}"
if ! grep -q "downloder.test" /etc/hosts; then
    echo "127.0.0.1 downloder.test downloader.test" >> /etc/hosts
    echo -e "${GREEN}✓ Added downloder.test to /etc/hosts${NC}"
fi

# 8. Configure & Restart Nginx
echo -e "${CYAN}[7/7] Configuring Nginx SSL Reverse Proxy & Systemd Service...${NC}"
NGINX_CONF="/etc/nginx/sites-available/downloder.test"
cp "$DEST_DIR/nginx/downloder.test.conf" "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx

# Configure Systemd Service
pkill -f "python3.*server/main.py" 2>/dev/null || true
cp "$DEST_DIR/deploy/video-downloader-local.service" /etc/systemd/system/video-downloader.service
systemctl daemon-reload
systemctl enable video-downloader.service
systemctl restart video-downloader.service

# Setup 15-Minute Cache Cleanup Cron for sumon user
CRON_JOB="*/15 * * * * find $DEST_DIR/server/downloads -type f -mmin +15 -delete 2>/dev/null"
(crontab -u sumon -l 2>/dev/null | grep -v "server/downloads" ; echo "$CRON_JOB") | crontab -u sumon -

echo ""
echo -e "${GREEN}===================================================================${NC}"
echo -e "${BOLD}${GREEN}   ✓ SETUP COMPLETED SUCCESSFULLY!                                 ${NC}"
echo -e "${BOLD}${CYAN}   ➜ Local URL: https://downloder.test                             ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo -e "  • Project Path:       ${BOLD}$DEST_DIR${NC}"
echo -e "  • Boot Auto-Start:    ${BOLD}ENABLED (systemd video-downloader.service)${NC}"
echo -e "  • 15-Min Cache Purge: ${BOLD}ACTIVE (engine + cron)${NC}"
echo -e "  • SSL Reverse Proxy:  ${BOLD}ACTIVE (nginx port 80 -> 443 -> 5000)${NC}"
echo ""
