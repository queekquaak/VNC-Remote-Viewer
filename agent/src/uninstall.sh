#!/bin/bash

set -e

YELLOW="\e[33m"
GREEN="\e[32m"
RESET="\e[0m"

# Checking permissions
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Run this script using root (sudo)${RESET}"
  exit 1
fi

# Dirs
INSTALL_DIR="/opt/vnc-rm-agent"
LOG_FILE="/var/log/vnc-rm-agent.log"
SERVICE_FILE="/etc/systemd/system/vnc-rm-agent.service"

echo "Stopping and disabling systemd service..."
systemctl stop vnc-rm-agent || true
systemctl disable vnc-rm-agent || true
systemctl daemon-reload

echo "Deleting service..."
rm -f "$SERVICE_FILE"

echo "Cleaning logs..."
rm -f "$LOG_FILE"

echo "Deleting agent's files..."
find "./" -mindepth 1 -path "./conf" -prune -o -name uninstall.sh -prune -o -exec rm -rf {} +

read -p "Delete configuration file? (y/n): " CONFIRM
if [[ "$CONFIRM" == "y" ]]; then
    echo -e "${GREEN}Configuration deleted.${RESET}"
    rm -rf "$INSTALL_DIR"
else
    echo -e "${YELLOW}Configuration saved.${RESET}"
fi

echo -e "${GREEN}Agent successfully uninstalled!${RESET}"
rm -f "./uninstall.sh"
