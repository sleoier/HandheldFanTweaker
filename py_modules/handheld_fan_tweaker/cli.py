"""Runs the plugin backend from a terminal, without Decky.

  PYTHONPATH=py_modules python3 -m handheld_fan_tweaker.cli state
  PYTHONPATH=py_modules python3 -m handheld_fan_tweaker.cli --root /tmp/hft --dry-run set silent "50:0,60:40,75:120,90:255"
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .composition import build_service
from .domain import FanCurvesError
from .infrastructure import parse_curve_text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hft", description="HandheldFanTweaker backend")
    parser.add_argument("--root", default="/", help="root for /etc, /usr and /var")
    parser.add_argument("--sys-root", default="/", help="root for /sys")
    parser.add_argument("--settings", default=os.path.expanduser("~/.cache/handheld-fan-tweaker-cli"))
    parser.add_argument("--dry-run", action="store_true", help="don't reload the daemon")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("state")
    sub.add_parser("telemetry")
    sub.add_parser("reconcile")
    set_cmd = sub.add_parser("set")
    set_cmd.add_argument("profile")
    set_cmd.add_argument("curve", help='e.g. "50:0,60:40,75:120,90:255"')
    reset_cmd = sub.add_parser("reset")
    reset_cmd.add_argument("profile")
    args = parser.parse_args(argv)

    service = build_service(args.settings, fs_root=args.root, sys_root=args.sys_root, dry_run=args.dry_run)
    try:
        if args.command == "state":
            result = service.state()
        elif args.command == "telemetry":
            result = service.telemetry()
        elif args.command == "reconcile":
            result = service.reconcile_on_start()
        elif args.command == "set":
            result = service.set_curve(args.profile, parse_curve_text(args.curve).to_pairs())
        else:
            result = service.reset_curve(args.profile)
    except (FanCurvesError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
