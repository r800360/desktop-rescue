from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    apply_plan,
    build_plan,
    desktop_status,
    undo_latest,
    write_report,
)

def default_desktop() -> Path:
    return Path.home() / "Desktop"

def add_common_args(parser: argparse.ArgumentParser):
    parser.add_argument("--desktop", type=Path, default=default_desktop(), help="Desktop path")
    parser.add_argument("--recent-days", type=int, default=7, help="Keep files modified within this many days in 00_INBOX_Recent")

def cmd_plan(args) -> int:
    desktop = args.desktop.expanduser().resolve()
    plans = build_plan(desktop, recent_days=args.recent_days)
    report = write_report(desktop, plans, dry_run=True)
    print(f"Dry-run complete. Planned moves: {len(plans)}")
    print(f"Report: {report}")
    return 0

def cmd_run(args) -> int:
    desktop = args.desktop.expanduser().resolve()
    plans = build_plan(desktop, recent_days=args.recent_days)

    if not args.yes:
        print("This will move Desktop items into _Desktop_Rescue.")
        print("A manifest will be created so you can undo the move.")
        print("Run again with --yes to confirm, or use `desktop-rescue plan` first.")
        return 2

    results, manifest = apply_plan(desktop, plans)
    report = write_report(desktop, results, dry_run=False)

    moved = [r for r in results if r.status == "moved"]
    failed = [r for r in results if r.status == "failed"]
    skipped = [r for r in results if r.status == "skipped"]

    print(f"Run complete.")
    print(f"Moved:   {len(moved)}")
    print(f"Failed:  {len(failed)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Manifest: {manifest}")
    print(f"Report: {report}")

    if failed:
        print("Some items failed. Check the report and error log in _Desktop_Rescue\\_reports.")

    return 1 if failed else 0

def cmd_undo(args) -> int:
    desktop = args.desktop.expanduser().resolve()
    count = undo_latest(desktop)
    print(f"Undo complete. Restored items: {count}")
    return 0

def cmd_status(args) -> int:
    desktop = args.desktop.expanduser().resolve()
    print(json.dumps(desktop_status(desktop), indent=2))
    return 0

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="desktop-rescue")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", help="Preview changes without moving anything")
    add_common_args(p_plan)
    p_plan.set_defaults(func=cmd_plan)

    p_run = sub.add_parser("run", help="Organize Desktop for real")
    add_common_args(p_run)
    p_run.add_argument("--yes", action="store_true", help="Actually move files")
    p_run.set_defaults(func=cmd_run)

    p_undo = sub.add_parser("undo", help="Undo the latest real run")
    p_undo.add_argument("--desktop", type=Path, default=default_desktop(), help="Desktop path")
    p_undo.set_defaults(func=cmd_undo)

    p_status = sub.add_parser("status", help="Show Desktop Rescue status")
    p_status.add_argument("--desktop", type=Path, default=default_desktop(), help="Desktop path")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
