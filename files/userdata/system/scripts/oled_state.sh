#!/bin/sh
STATE="/tmp/oled.state"

EVENT="$1"
SYSTEM="$2"
EMULATOR="$3"
CORE="$4"
ROM="$5"

case "$EVENT" in
  gameStart)
    printf "mode=game\nsystem=%s\nrom=%s\n" "$SYSTEM" "$ROM" > "$STATE"
    ;;
  gameStop)
    printf "mode=menu\n" > "$STATE"
    ;;
esac
