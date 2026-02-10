#!/bin/sh
set -e

echo "[+] Installing Batocera OLED daemon..."

# Create dirs
mkdir -p /userdata/system/bin /userdata/system/scripts /userdata/system/services /userdata/system/logs

# Copy files
cp -f files/userdata/system/bin/oled_daemon.py /userdata/system/bin/oled_daemon.py
cp -f files/userdata/system/scripts/oled_state.sh /userdata/system/scripts/oled_state.sh
cp -f files/userdata/system/services/OLED_DAEMON /userdata/system/services/OLED_DAEMON

chmod +x /userdata/system/bin/oled_daemon.py
chmod +x /userdata/system/scripts/oled_state.sh
chmod +x /userdata/system/services/OLED_DAEMON

# Clear caches
rm -f /tmp/oled.marquee.raw /tmp/oled.marquee.key

echo "[+] Installed."
echo ""
echo "Next steps:"
echo "1) Batocera UI -> System Settings -> Services -> OLED_DAEMON -> ON"
echo "2) Reboot (recommended)."
echo ""
echo "Manual start (optional): /userdata/system/services/OLED_DAEMON start"
