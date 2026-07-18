import os
import time
from pathlib import Path

import frappe


def ensure_dirs():
    for path in (sessions_dir(), temp_dir()):
        Path(path).mkdir(parents=True, exist_ok=True)


def sessions_dir():
    return frappe.get_site_path("private", "telegram_drive", "sessions")


def temp_dir():
    return frappe.get_site_path("private", "telegram_drive", "temp")


def safe_temp_path(filename):
    ensure_dirs()
    base = Path(temp_dir()).resolve()
    target = (base / Path(filename).name).resolve()
    if base not in target.parents and target != base:
        frappe.throw("Invalid temp file path")
    return str(target)


def list_temp():
    ensure_dirs()
    rows = []
    for item in Path(temp_dir()).iterdir():
        if item.is_file():
            stat = item.stat()
            rows.append(
                {
                    "name": item.name,
                    "filename": item.name,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "modified_at": stat.st_mtime,
                }
            )
    return sorted(rows, key=lambda row: row["modified"], reverse=True)


def cleanup_old(hours=None):
    if hours is None:
        hours = frappe.db.get_single_value("Telegram Drive Setting", "temp_retention_hours") or 6
    cutoff = time.time() - int(hours) * 3600
    removed = []
    for row in list_temp():
        if row["modified"] < cutoff:
            path = safe_temp_path(row["filename"])
            os.remove(path)
            removed.append(row["filename"])
    return removed
