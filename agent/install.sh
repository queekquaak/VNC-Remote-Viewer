#!/bin/bash

set -e  # Error stop

RED="\e[31m"
YELLOW="\e[33m"
GREEN="\e[32m"
RESET="\e[0m"

install_deps() {
    case "$PKG_MANAGER" in
        apt)
            apt update -y
            apt install -y x11vnc snapd coreutils build-essential libssl-dev libffi-dev python3-dev python3-venv
            ;;
        dnf)
            dnf update -y
            dnf install -y x11vnc snapd coreutils make automake gcc gcc-c++ kernel-devel openssl-devel libffi-devel python3-devel python3-virtualenv python3-pip
            ;;
        yum)
            yum update -y
            yum install -y x11vnc snapd coreutils make automake gcc gcc-c++ kernel-devel openssl-devel libffi-devel python3-devel python3-virtualenv python3-pip
            ;;
        pacman)
            pacman -Sy --noconfirm x11vnc snapd coreutils base-devel python python-virtualenv python3-pip openssl libffi
            ;;
        zypper)
            zypper refresh -y
            zypper install -y x11vnc snapd coreutils make automake gcc gcc-c++ kernel-devel libopenssl-devel libffi-devel python3-devel python3-virtualenv python3-pip
            ;;
    esac
}


# Checking permissions
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Run this script using root (sudo)${RESET}"
  exit 1
fi

# Checking systemd
if pidof systemd &> /dev/null && [ -d /etc/systemd/system ]; then
  :
else
  echo -e "${RED}Error: Systemd not installed. Check documentation and try again.${RESET}"
  exit 1
fi

# Checking python version
if ! command -v "python3" &> /dev/null; then
  echo -e "${RED}Python3 not installed. Please, install Python3.${RESET}"
  exit 1
fi
PYTHON_VERSION=$(python3 -V 2>&1 | cut -d' ' -f2)
MAJOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR_VERSION=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$MAJOR_VERSION" -gt 3 ] || { [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 7 ]; }; then
  :
else
  echo -e "${RED}Agent needs Python 3.7+, installed version is '$PYTHON_VERSION'${RESET}"
  echo -e "${YELLOW}Read your OS documentation and update it by yourself${RESET}"
  exit 1
fi

# Checking args
PKG_MANAGER=""
case "$1" in
  --apt) PKG_MANAGER="apt" ;;
  --dnf) PKG_MANAGER="dnf" ;;
  --yum) PKG_MANAGER="yum" ;;
  --pacman) PKG_MANAGER="pacman" ;;
  --zypper) PKG_MANAGER="zypper" ;;
  --custom) PKG_MANAGER="custom";;
  *)
    echo -e "${RED}Error: Unknown pkg manager.\nUsing: sudo bash $0 [--apt | --dnf | --yum | --pacman | --zypper]${RESET}"
    echo "Use --custom if you want to install these dependencies by yourself:"
    echo "x11vnc, novnc (from snap), coreutils, make, automake, gcc, g++ (or gcc-c++), kernel, headers"
    echo "websockify, openssl-dev, libffi-dev, python3-dev, python3-venv (or python3-virtualenv)"
    exit 1
    ;;
esac

# Checking pkg installation
if ! command -v "$PKG_MANAGER" &> /dev/null; then
  echo -e "${RED}Error: The specified package manager '$PKG_MANAGER' was not found in the system.${RESET}"
  echo -e "${YELLOW}Check the correctness or set dependencies manually.${RESET}"
  exit 1
elif [ "$PKG_MANAGER" == "custom" ]; then
  :
else
  echo "Installing dependencies..."
  install_deps
fi

# Checking snap installation
if ! command -v "snap" &> /dev/null; then
  echo -e "${RED}Snapd not installed. Please, install snapd.${RESET}"
  exit 1
else
  echo -e "${YELLOW}Starting snapd services...${RESET}"
  systemctl daemon-reload
  systemctl enable --now snapd.socket
  systemctl enable --now snapd.service
  sleep 10
  snap install novnc
fi

# Installing systemd
SERVICE_FILE="/etc/systemd/system/vnc-rm-agent.service"
cp ./src/vnc-rm-agent.service "$SERVICE_FILE"
systemctl daemon-reload
echo -e "${YELLOW}Systemd vnc-rm-agent.service installed.${RESET}"

# Dirs
INSTALL_DIR="/opt/vnc-rm-agent"
MOD_DIR="$INSTALL_DIR/modules"
CONF_DIR="$INSTALL_DIR/conf"
LOG_DIR="$INSTALL_DIR/log"

# Catalogues
echo "Creating catalogues..."
mkdir -p "$INSTALL_DIR" "$MOD_DIR" "$CONF_DIR" "$LOG_DIR"

# Copying files
echo "Copying scripts..."
find ./src -type f -name "*.py" -exec sed -i 's/\r$//' {} \;
cp ./src/__main__.py "$INSTALL_DIR/"
cp ./src/uninstall.sh "$INSTALL_DIR/"
cp -r ./src/modules/* "$MOD_DIR/"
chmod +x "$INSTALL_DIR/__main__.py" "$INSTALL_DIR/uninstall.sh"

# Virtual env setup
echo "Creating virtual env..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "./conf/requirements.txt"

# Copying config
CONFIG_FILE="$CONF_DIR/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Creating default config...${RESET}"
    cp ./conf/config.yaml "$CONF_DIR/"
else
  echo -e "${YELLOW}Config file already exists.${RESET}"
fi

# Creating log
echo -e "${YELLOW}Preparing logs...${RESET}"
LOG_FILE="$LOG_DIR/vnc-rm-agent.log"
touch "$LOG_FILE"

# Setting access rights
chown -R root:root "$INSTALL_DIR"
chmod -R 700 "$INSTALL_DIR"

echo -e "${GREEN}\nAgent installed successfully at '$INSTALL_DIR'"
echo -e "\nCheck or edit conf file before run '$CONF_DIR/config.yaml'"
echo -e "\nTo start agent enter 'sudo systemctl enable --now vnc-rm-agent.service'${RESET}\n"
