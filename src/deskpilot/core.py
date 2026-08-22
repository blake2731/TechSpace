from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

CATEGORY_MAP = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods"},
    "Archives": {".zip", ".7z", ".rar", ".tar", ".gz"},
    "Installers": {".exe", ".msi", ".msix", ".appx"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"},
    "Video": {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"},
    "Code": {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".cs", ".html", ".css", ".json", ".yaml", ".yml", ".ps1", ".bat"},
}
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".idea", ".vscode"}
TEMP_SUFFIXES = {".tmp", ".part", ".crdownload", ".download"}
SCREENSHOT_WORDS = ("screenshot", "screen shot", "snipping")

@dataclass(frozen=True)
class MovePlan:
    source: Path
    destination: Path
    category: str

@dataclass(frozen=True)
class AttentionItem:
    path: Path
    reason: str
    size: int
    modified: datetime
    severity: int

def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".deskpilot"))
    path = base / "DeskPilot"
    path.mkdir(parents=True, exist_ok=True)
    return path

def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in CATEGORY_MAP.items():
        if suffix in extensions:
            return category
    return "Other"

def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

def build_organize_plan(folder: Path) -> list[MovePlan]:
    folder = folder.expanduser().resolve()
    plans = []
    for item in folder.iterdir():
        if item.is_file():
            category = category_for(item)
            plans.append(MovePlan(item, unique_destination(folder / category / item.name), category))
    return sorted(plans, key=lambda p: (p.category.lower(), p.source.name.lower()))

def apply_organize_plan(plans: Iterable[MovePlan]) -> Path:
    records = []
    for plan in plans:
        plan.destination.parent.mkdir(parents=True, exist_ok=True)
        final_destination = unique_destination(plan.destination)
        shutil.move(str(plan.source), str(final_destination))
        records.append({"source": str(plan.source), "destination": str(final_destination)})
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    undo_file = app_data_dir() / f"undo_{stamp}.json"
    undo_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return undo_file

def latest_undo_file() -> Path | None:
    files = sorted(app_data_dir().glob("undo_*.json"), reverse=True)
    return files[0] if files else None

def undo_file_moves(undo_file: Path) -> tuple[int, list[str]]:
    records = json.loads(undo_file.read_text(encoding="utf-8"))
    restored, problems = 0, []
    for record in reversed(records):
        source, destination = Path(record["source"]), Path(record["destination"])
        if not destination.exists():
            problems.append(f"Missing: {destination}")
            continue
        source.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            source = unique_destination(source)
        shutil.move(str(destination), str(source))
        restored += 1
    if not problems:
        undo_file.unlink(missing_ok=True)
    return restored, problems

def iter_files(folder: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(root) / name
            try:
                if path.is_file():
                    yield path
            except OSError:
                continue

def quick_search(folder: Path, text: str, limit: int = 500) -> list[Path]:
    query = text.lower().strip()
    if not query:
        return []
    matches = []
    for path in iter_files(folder):
        if query in path.name.lower():
            matches.append(path)
            if len(matches) >= limit:
                break
    return sorted(matches, key=lambda p: p.name.lower())

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()

def find_duplicates(folder: Path, min_size: int = 1) -> list[list[Path]]:
    by_size = {}
    for path in iter_files(folder):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= min_size:
            by_size.setdefault(size, []).append(path)
    groups = []
    for paths in by_size.values():
        if len(paths) < 2:
            continue
        by_hash = {}
        for path in paths:
            try:
                by_hash.setdefault(sha256_file(path), []).append(path)
            except (OSError, PermissionError):
                continue
        groups.extend(group for group in by_hash.values() if len(group) > 1)
    return sorted(groups, key=lambda g: sum(p.stat().st_size for p in g), reverse=True)

def large_stale_files(folder: Path, min_mb: int = 100, older_than_days: int = 90):
    threshold_size = min_mb * 1024 * 1024
    cutoff = datetime.now() - timedelta(days=older_than_days)
    results = []
    for path in iter_files(folder):
        try:
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
            if stat.st_size >= threshold_size and modified <= cutoff:
                results.append((path, stat.st_size, modified))
        except (OSError, PermissionError):
            continue
    return sorted(results, key=lambda x: x[1], reverse=True)

def recent_activity(folder: Path, days: int = 7, limit: int = 250):
    cutoff = datetime.now() - timedelta(days=max(0, days))
    results = []
    for path in iter_files(folder):
        try:
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
            if modified >= cutoff:
                results.append((path, stat.st_size, modified, category_for(path)))
        except (OSError, PermissionError):
            continue
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]

def attention_queue(folder: Path, now: datetime | None = None, limit: int = 300) -> list[AttentionItem]:
    now = now or datetime.now()
    items = []
    for path in iter_files(folder):
        try:
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
        except (OSError, PermissionError):
            continue
        age_days = max(0, (now - modified).days)
        suffix = path.suffix.lower()
        lower_name = path.name.lower()
        reason = None
        severity = 0
        if stat.st_size == 0:
            reason, severity = "Empty file", 3
        elif suffix in TEMP_SUFFIXES and age_days >= 1:
            reason, severity = "Leftover partial or temporary download", 3
        elif category_for(path) == "Installers" and age_days >= 14:
            reason, severity = f"Installer is {age_days} days old", 2
        elif category_for(path) == "Archives" and age_days >= 30:
            reason, severity = f"Archive is {age_days} days old", 2
        elif stat.st_size >= 1024 * 1024 * 1024 and age_days >= 30:
            reason, severity = "Large file over 1 GB has gone cold", 2
        elif any(word in lower_name for word in SCREENSHOT_WORDS) and age_days >= 21:
            reason, severity = f"Old screenshot is {age_days} days old", 1
        if reason:
            items.append(AttentionItem(path, reason, stat.st_size, modified, severity))
    return sorted(items, key=lambda x: (-x.severity, x.modified, -x.size))[:limit]

def folder_snapshot(folder: Path) -> dict:
    files = 0
    total_bytes = 0
    categories: dict[str, int] = {}
    extensions: dict[str, int] = {}
    newest: tuple[Path, datetime] | None = None
    for path in iter_files(folder):
        try:
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime)
        except (OSError, PermissionError):
            continue
        files += 1
        total_bytes += stat.st_size
        category = category_for(path)
        categories[category] = categories.get(category, 0) + 1
        ext = path.suffix.lower() or "(none)"
        extensions[ext] = extensions.get(ext, 0) + 1
        if newest is None or modified > newest[1]:
            newest = (path, modified)
    return {
        "files": files,
        "bytes": total_bytes,
        "categories": dict(sorted(categories.items(), key=lambda kv: (-kv[1], kv[0]))),
        "extensions": dict(sorted(extensions.items(), key=lambda kv: (-kv[1], kv[0]))[:10]),
        "newest": newest,
    }

def handoff_file() -> Path:
    return app_data_dir() / "handoffs.json"

def load_handoffs() -> dict[str, str]:
    try:
        data = json.loads(handoff_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def save_handoff(folder: Path, text: str) -> None:
    data = load_handoffs()
    key = str(folder.expanduser().resolve())
    text = text.strip()
    if text:
        data[key] = text
    else:
        data.pop(key, None)
    handoff_file().write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_handoff(folder: Path) -> str:
    return load_handoffs().get(str(folder.expanduser().resolve()), "")
