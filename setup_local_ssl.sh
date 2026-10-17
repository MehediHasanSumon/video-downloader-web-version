#!/usr/bin/env bash
# ====================================================================
#  Universal Video Downloader Pro - Local Setup with SSL & Nginx
#  Domain: https://downloder.test
# ====================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}===================================================================${NC}"
echo -e "${BOLD}   Video Downloader Pro - Local Setup (https://downloder.test)     ${NC}"
echo -e "${CYAN}===================================================================${NC}"
echo ""

# 1. Require sudo/root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run with sudo: sudo bash setup_local_ssl.sh${NC}"
    exit 1
fi

PROJECT_DIR="/home/sumon/Desktop/Youtube/web-version"
cd "$PROJECT_DIR"

# 2. Install Nginx & OpenSSL if missing
echo -e "${CYAN}[1/6] Checking system packages (Nginx & OpenSSL)...${NC}"
if ! command -v nginx >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing Nginx...${NC}"
    apt-get update -y
    apt-get install -y nginx
fi

# 3. Generate SSL Certificates for downloder.test if not present
echo -e "${CYAN}[2/6] Configuring SSL Certificates...${NC}"
mkdir -p "$PROJECT_DIR/certs"
if [ ! -f "$PROJECT_DIR/certs/downloder.test.crt" ]; then
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
      -keyout "$PROJECT_DIR/certs/downloder.test.key" \
      -out "$PROJECT_DIR/certs/downloder.test.crt" \
      -subj "/C=BD/ST=Dhaka/L=Dhaka/O=VideoDownloader/CN=downloder.test" \
      -addext "subjectAltName=DNS:downloder.test,DNS:downloader.test,DNS:localhost,IP:127.0.0.1"
fi
chmod 644 "$PROJECT_DIR/certs/downloder.test.crt"
chmod 600 "$PROJECT_DIR/certs/downloder.test.key"

# Also trust certificate locally in system trust store (Ubuntu ca-certificates)
mkdir -p /usr/local/share/ca-certificates/extra
cp "$PROJECT_DIR/certs/downloder.test.crt" /usr/local/share/ca-certificates/extra/downloder.test.crt
update-ca-certificates >/dev/null 2>&1 || true

# 4. Update /etc/hosts to resolve downloder.test to 127.0.0.1
echo -e "${CYAN}[3/6] Mapping downloder.test in /etc/hosts...${NC}"
if ! grep -q "downloder.test" /etc/hosts; then
    echo "127.0.0.1 downloder.test downloader.test" >> /etc/hosts
    echo -e "${GREEN}✓ Added downloder.test to /etc/hosts${NC}"
else
    echo -e "${GREEN}✓ downloder.test already in /etc/hosts${NC}"
fi

# 5. Configure Nginx Reverse Proxy with SSL
echo -e "${CYAN}[4/6] Setting up Nginx Virtual Host...${NC}"
NGINX_CONF="/etc/nginx/sites-available/downloder.test"
cp "$PROJECT_DIR/nginx/downloder.test.conf" "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/

# Remove default site if conflicting
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx

# 6. Configure Systemd Service to auto-run on startup
echo -e "${CYAN}[5/6] Configuring Systemd Startup Service...${NC}"
SERVICE_FILE="/etc/systemd/system/video-downloader.service"
cp "$PROJECT_DIR/deploy/video-downloader-local.service" "$SERVICE_FILE"

# Stop any old manual instances of python server
pkill -f "python3.*server/main.py" || true

systemctl daemon-reload
systemctl enable video-downloader.service
systemctl restart video-downloader.service

# 7. Configure 15-Minute Cache Cleanup Cron
echo -e "${CYAN}[6/6] Configuring 15-minute Cache Purge Cron...${NC}"
CRON_JOB="*/15 * * * * find $PROJECT_DIR/server/downloads -type f -mmin +15 -delete 2>/dev/null"
(crontab -l 2>/dev/null | grep -v "server/downloads" ; echo "$CRON_JOB") | crontab -

echo ""
echo -e "${GREEN}===================================================================${NC}"
echo -e "${BOLD}${GREEN}   ✓ SETUP COMPLETE! App is live with SSL at:                      ${NC}"
echo -e "${BOLD}${CYAN}   ➜ https://downloder.test                                        ${NC}"
echo -e "${GREEN}===================================================================${NC}"
echo -e "  • Auto-start on boot:  ${BOLD}ENABLED (systemd)${NC}"
echo -e "  • 15-minute cache purge: ${BOLD}ACTIVE (engine + cron)${NC}"
echo -e "  • SSL Reverse Proxy:   ${BOLD}ACTIVE (nginx port 443 -> 5000)${NC}"
echo ""
