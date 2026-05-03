from __future__ import annotations

import json
import shutil
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from .rules import RESCUE_ROOT_NAME, SKIP_NAMES, category_for

@dataclass
class MovePlan:
    src: str
    dst: str
    category: str
    reason: str

@dataclass
class MoveResult:
    src: str
    dst: str
    category: str
    status: str
    error: str = ""

def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def safe_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 2

    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False

def is_desktop_item_safe_to_move(path: Path, desktop: Path) -> bool:
    lower = path.name.lower()
    rescue_root = desktop / RESCUE_ROOT_NAME

    if lower in SKIP_NAMES:
        return False

    if path.resolve() == rescue_root.resolve():
        return False

    if is_relative_to(path, rescue_root):
        return False

    if path.name.startswith("."):
        return False

    return True

def is_recent(path: Path, recent_days: int) -> bool:
    if recent_days <= 0:
        return False

    cutoff = datetime.now() - timedelta(days=recent_days)

    try:
        modified = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return False

    return modified >= cutoff

def iter_desktop_items(desktop: Path):
    for item in desktop.iterdir():
        if is_desktop_item_safe_to_move(item, desktop):
            yield item

def validate_move(src: Path, dst: Path, desktop: Path) -> tuple[bool, str]:
    rescue_root = desktop / RESCUE_ROOT_NAME

    if not src.exists():
        return False, "source no longer exists"

    if src.resolve() == rescue_root.resolve():
        return False, "refusing to move rescue root"

    if is_relative_to(src, rescue_root):
        return False, "refusing to move item already inside rescue root"

    if is_relative_to(dst, src):
        return False, "refusing to move a directory into itself"

    if src.resolve() == dst.resolve():
        return False, "source and destination are identical"

    return True, ""

def build_plan(desktop: Path, recent_days: int = 7) -> list[MovePlan]:
    desktop = desktop.expanduser().resolve()
    rescue_root = desktop / RESCUE_ROOT_NAME
    plans: list[MovePlan] = []

    for item in iter_desktop_items(desktop):
        recent = is_recent(item, recent_days)
        category = category_for(item, is_recent=recent)
        dst_dir = rescue_root / category
        dst = safe_unique_path(dst_dir / item.name)

        ok, reason = validate_move(item, dst, desktop)
        if not ok:
            continue

        move_reason = "recent item kept easy to find" if recent else f"classified as {category}"
        plans.append(MovePlan(str(item), str(dst), category, move_reason))

    plans.sort(key=lambda p: (p.category, Path(p.src).name.lower()))
    return plans

def ensure_dirs(desktop: Path) -> Path:
    rescue_root = desktop / RESCUE_ROOT_NAME

    categories = [
        "00_INBOX_Recent",
        "01_Shortcuts",
        "02_PDFs",
        "03_School",
        "04_Projects_Code",
        "05_Archives_Zips_Tars",
        "06_Images_Media",
        "07_Notebooks_Data",
        "08_Installers_Config",
        "09_Apps_Tools",
        "90_Old_Folders",
        "99_Unsorted",
        "_reports",
    ]

    for category in categories:
        (rescue_root / category).mkdir(parents=True, exist_ok=True)

    return rescue_root

def reports_dir(desktop: Path) -> Path:
    return ensure_dirs(desktop) / "_reports"

def write_report(desktop: Path, plans: list[MovePlan | MoveResult], dry_run: bool) -> Path:
    report_dir = reports_dir(desktop)
    stamp = timestamp()
    report = report_dir / (f"plan_{stamp}.txt" if dry_run else f"run_{stamp}.txt")

    counts: dict[str, int] = {}
    for p in plans:
        counts[p.category] = counts.get(p.category, 0) + 1

    lines = []
    lines.append("Desktop Rescue Report")
    lines.append("=" * 22)
    lines.append(f"Mode: {'DRY RUN' if dry_run else 'REAL RUN'}")
    lines.append(f"Desktop: {desktop}")
    lines.append(f"Total planned moves: {len(plans)}")
    lines.append("")
    lines.append("Category counts:")

    for category, count in sorted(counts.items()):
        lines.append(f"  {category}: {count}")

    lines.append("")
    lines.append("Moves:")

    for p in plans:
        lines.append(f"[{p.category}]")
        lines.append(f"  FROM: {p.src}")
        lines.append(f"  TO:   {p.dst}")

        if isinstance(p, MoveResult):
            lines.append(f"  STATUS: {p.status}")
            if p.error:
                lines.append(f"  ERROR:  {p.error}")
        else:
            lines.append(f"  WHY:  {p.reason}")

        lines.append("")

    report.write_text("\n".join(lines), encoding="utf-8")
    latest = report_dir / "latest_plan.txt"
    latest.write_text("\n".join(lines), encoding="utf-8")

    return report

def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def start_manifest(desktop: Path, plans: list[MovePlan]) -> Path:
    report_dir = reports_dir(desktop)
    manifest = report_dir / f"manifest_{timestamp()}.json"

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "completed_at": None,
        "desktop": str(desktop),
        "status": "in_progress",
        "planned": [asdict(p) for p in plans],
        "results": [],
    }

    write_json(manifest, payload)
    write_json(report_dir / "latest_manifest.json", payload)

    return manifest

def append_manifest_result(manifest: Path, result: MoveResult) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["results"].append(asdict(result))

    write_json(manifest, payload)
    latest = manifest.parent / "latest_manifest.json"
    write_json(latest, payload)

def finish_manifest(manifest: Path) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["completed_at"] = datetime.now().isoformat(timespec="seconds")

    failures = [r for r in payload["results"] if r.get("status") != "moved"]
    payload["status"] = "completed_with_errors" if failures else "completed"

    write_json(manifest, payload)
    latest = manifest.parent / "latest_manifest.json"
    write_json(latest, payload)

def apply_plan(desktop: Path, plans: list[MovePlan]) -> tuple[list[MoveResult], Path]:
    ensure_dirs(desktop)
    manifest = start_manifest(desktop, plans)
    results: list[MoveResult] = []

    for p in plans:
        src = Path(p.src)
        dst = safe_unique_path(Path(p.dst))

        ok, validation_error = validate_move(src, dst, desktop)
        if not ok:
            result = MoveResult(
                src=str(src),
                dst=str(dst),
                category=p.category,
                status="skipped",
                error=validation_error,
            )
            results.append(result)
            append_manifest_result(manifest, result)
            continue

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

            result = MoveResult(
                src=str(src),
                dst=str(dst),
                category=p.category,
                status="moved",
            )

        except Exception as exc:
            result = MoveResult(
                src=str(src),
                dst=str(dst),
                category=p.category,
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
            )

            error_log = reports_dir(desktop) / f"error_{timestamp()}.txt"
            error_log.write_text(traceback.format_exc(), encoding="utf-8")

        results.append(result)
        append_manifest_result(manifest, result)

    finish_manifest(manifest)
    return results, manifest

def latest_manifest_path(desktop: Path) -> Path:
    return desktop / RESCUE_ROOT_NAME / "_reports" / "latest_manifest.json"

def undo_latest(desktop: Path) -> int:
    manifest_path = latest_manifest_path(desktop)

    if not manifest_path.exists():
        raise FileNotFoundError(f"No latest manifest found at {manifest_path}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = payload.get("results", [])

    undone = 0

    for item in reversed(results):
        if item.get("status") != "moved":
            continue

        original = Path(item["src"])
        current = Path(item["dst"])

        if not current.exists():
            continue

        target = safe_unique_path(original)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(target))
        undone += 1

    undo_report = reports_dir(desktop) / f"undo_{timestamp()}.txt"
    undo_report.write_text(
        f"Undone moves: {undone}\nManifest: {manifest_path}\n",
        encoding="utf-8",
    )

    return undone

def desktop_status(desktop: Path) -> dict:
    desktop = desktop.expanduser().resolve()
    rescue_root = desktop / RESCUE_ROOT_NAME

    visible_items = [
        p for p in desktop.iterdir()
        if is_desktop_item_safe_to_move(p, desktop)
    ]

    latest_manifest = latest_manifest_path(desktop)

    status = {
        "desktop": str(desktop),
        "visible_items_outside_rescue": len(visible_items),
        "rescue_root_exists": rescue_root.exists(),
        "latest_manifest_exists": latest_manifest.exists(),
    }

    if latest_manifest.exists():
        payload = json.loads(latest_manifest.read_text(encoding="utf-8"))
        status["latest_manifest_status"] = payload.get("status")
        status["latest_manifest_results"] = len(payload.get("results", []))

    return status