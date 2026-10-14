#!/bin/sh
# Installs or updates HandheldFanTweaker from the latest GitHub release.
# Usage: curl -fsSL https://raw.githubusercontent.com/sleoier/HandheldFanTweaker/main/update.sh | sudo sh
set -e
API="https://api.github.com/repos/sleoier/HandheldFanTweaker/releases/latest"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run it with sudo." >&2
  exit 1
fi
USER_HOME="$(getent passwd "${SUDO_USER:-$(id -un)}" | cut -d: -f6)"
PLUGINS="$USER_HOME/homebrew/plugins"
DEST="$PLUGINS/HandheldFanTweaker"
[ -d "$PLUGINS" ] || { echo "Decky Loader isn't installed ($PLUGINS not found)." >&2; exit 1; }

version() { python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$1" 2>/dev/null || echo "none"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Asked to the API: the releases/latest/download redirect can lag behind a new release.
URL="$(curl -fsSL "$API" | python3 -c 'import json, sys
for asset in json.load(sys.stdin).get("assets", []):
    if asset["name"] == "HandheldFanTweaker.zip":
        print(asset["browser_download_url"])')"
[ -n "$URL" ] || { echo "Couldn't find HandheldFanTweaker.zip in the latest release." >&2; exit 1; }
echo "Downloading $URL"
curl -fsSL -o "$TMP/plugin.zip" "$URL"
python3 -m zipfile -e "$TMP/plugin.zip" "$TMP/x"
[ -f "$TMP/x/HandheldFanTweaker/plugin.json" ] || { echo "The release zip doesn't look like this plugin." >&2; exit 1; }

OLD="$(version "$DEST/package.json")"
NEW="$(version "$TMP/x/HandheldFanTweaker/package.json")"
rm -rf "$DEST"
mv "$TMP/x/HandheldFanTweaker" "$DEST"
chown -R root:root "$DEST"
systemctl restart plugin_loader
echo "HandheldFanTweaker $OLD -> $NEW installed. Decky restarted."
