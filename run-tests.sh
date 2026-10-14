#!/bin/sh
# On-device checks. Read-only on the system: writes are tested on a copy of
# the config in /tmp/hft. The report goes to ~/Downloads/hft-report.txt.
cd "$(dirname "$0")" || exit 1
OUT="$HOME/Downloads/hft-report.txt"
export PYTHONPATH="$PWD/py_modules"
mkdir -p "$HOME/Downloads"

{
echo "== HandheldFanTweaker report $(date)"
echo "== system"
uname -a
python3 --version
tr -d '\0' < /sys/firmware/devicetree/base/model 2>/dev/null; echo

echo "== daemons"
for unit in odin3d konkrd plugin_loader; do printf '%s: %s\n' "$unit" "$(systemctl is-active "$unit" 2>&1)"; done
ls -l /usr/lib/odin3/odin3d /usr/lib/konkr/konkrd /etc/odin3.conf /etc/konkrd.conf 2>&1

echo "== odin3ctl status"
odin3ctl status 2>&1 | head -40

echo "== thermal zones (type, milli-°C)"
for z in /sys/class/thermal/thermal_zone*; do
  printf '%s %s %s\n' "${z##*/}" "$(cat "$z/type" 2>/dev/null)" "$(cat "$z/temp" 2>/dev/null)"
done

echo "== hwmon"
for h in /sys/class/hwmon/hwmon*; do
  printf '%s %s pwm1=%s fan1_input=%s\n' "${h##*/}" "$(cat "$h/name" 2>/dev/null)" "$(cat "$h/pwm1" 2>/dev/null)" "$(cat "$h/fan1_input" 2>/dev/null)"
done

echo "== decky"
ls -ld "$HOME/homebrew" "$HOME/homebrew/plugins" 2>&1
ls "$HOME/homebrew/plugins" 2>&1

echo "== unit tests"
python3 -m unittest discover -s tests -t . -v 2>&1

echo "== cli: real state (read-only)"
python3 -m handheld_fan_tweaker.cli --settings /tmp/hft-settings state 2>&1

echo "== cli: writes on a copy in /tmp/hft"
rm -rf /tmp/hft /tmp/hft-settings-sbx
mkdir -p /tmp/hft/etc /tmp/hft/usr/lib/odin3
cp /etc/odin3.conf /tmp/hft/etc/ && touch /tmp/hft/usr/lib/odin3/odin3d
CLI="python3 -m handheld_fan_tweaker.cli --root /tmp/hft --settings /tmp/hft-settings-sbx --dry-run"
echo "-- set silent (valid)"
$CLI set silent "50:0,60:40,75:120,90:255" 2>&1
grep -n '^silent' /tmp/hft/etc/odin3.conf
echo "-- set silent (invalid, has to fail)"
$CLI set silent "50:0,99:200" 2>&1
echo "-- reset silent"
$CLI reset silent 2>&1
if diff /etc/odin3.conf /tmp/hft/etc/odin3.conf; then
  echo "RESULT: the copy matches the original after reset"
else
  echo "RESULT: the copy does NOT match the original (see diff above)"
fi
ls -l /tmp/hft/etc/
echo "== end"
} > "$OUT" 2>&1

echo "Done. Report: $OUT"
