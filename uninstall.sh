#!/bin/sh
set -e

echo "[-] Uninstalling Batocera OLED daemon..."

# Stop service if running
if [ -x /userdata/system/services/OLED_DAEMON ]; then
  /userdata/system/services/OLED_DAEMON stop || true
fi

rm -f /userdata/system/bin/oled_daemon.py
rm -f /userdata/system/scripts/oled_state.sh
rm -f /userdata/system/services/OLED_DAEMON

rm -f /tmp/oled.marquee.raw /tmp/oled.marquee.key
rm -f /userdata/system/logs/oled_daemon.log

echo "[-] Removed."
echo "Note: If you enabled OLED_DAEMON in the Batocera Services menu, turn it OFF there too."
