#!/bin/sh
# Installs or updates HandheldFanTweaker in Decky Loader.
# Usage: sudo sh install-on-device.sh
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
USER_HOME="$(getent passwd "${SUDO_USER:-$(id -un)}" | cut -d: -f6)"
DEST="$USER_HOME/homebrew/plugins/HandheldFanTweaker"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run it with sudo: sudo sh $0" >&2
  exit 1
fi
for f in plugin.json package.json main.py dist/index.js py_modules/handheld_fan_tweaker/__init__.py; do
  [ -e "$SRC/$f" ] || { echo "Missing $f in $SRC" >&2; exit 1; }
done

rm -rf "$DEST"
mkdir -p "$DEST"
cp -r "$SRC/plugin.json" "$SRC/package.json" "$SRC/main.py" "$SRC/py_modules" "$SRC/dist" "$DEST/"
for f in README.md LICENSE; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DEST/"; done
find "$DEST" -name '__pycache__' -type d -prune -exec rm -rf {} +
chown -R root:root "$DEST"

systemctl restart plugin_loader
echo "HandheldFanTweaker installed in $DEST and Decky restarted."
