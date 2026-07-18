import shutil
import sqlite3
from pathlib import Path

import frappe
from frappe.utils import now_datetime

from telegram_drive.services.temp_files import sessions_dir


def execute(sqlite_path, session_source=None):
    """Import legacy SQLite metadata without re-uploading Telegram files."""
    if not Path(sqlite_path).exists():
        frappe.throw(f"SQLite database not found: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    counts = {}
    try:
        counts["folders"] = _folders(conn)
        counts["files"] = _files(conn)
        counts["portal_users"] = _portal_users(conn)
        counts["shares"] = _shares(conn)
        counts["notes"] = _notes(conn)
        _settings(conn)
    finally:
        conn.close()
    if session_source:
        target = Path(sessions_dir())
        target.mkdir(parents=True, exist_ok=True)
        for item in Path(session_source).glob("*"):
            if item.is_file():
                shutil.copy2(item, target / item.name)
    frappe.db.commit()
    return counts


def _table(conn, name):
    try:
        return conn.execute(f"select * from {name}").fetchall()
    except sqlite3.OperationalError:
        return []


def _folders(conn):
    id_map = {}
    rows = _table(conn, "folders")
    for row in rows:
        doc = frappe.get_doc({"doctype": "Telegram Drive Folder", "folder_name": row["name"] if "name" in row.keys() else row["folder_name"], "created_at": row["created_at"] if "created_at" in row.keys() else now_datetime()})
        doc.insert(ignore_permissions=True)
        id_map[str(row["id"])] = doc.name
    for row in rows:
        parent = row["parent_id"] if "parent_id" in row.keys() else row["parent_folder"]
        if parent:
            frappe.db.set_value("Telegram Drive Folder", id_map[str(row["id"])], "parent_folder", id_map.get(str(parent)))
    frappe.cache().set_value("telegram_drive:migration:folder_map", id_map)
    return len(rows)


def _files(conn):
    id_map = frappe.cache().get_value("telegram_drive:migration:folder_map") or {}
    rows = _table(conn, "files")
    for row in rows:
        folder_id = row["folder_id"] if "folder_id" in row.keys() else row["folder"]
        frappe.get_doc({
            "doctype": "Telegram Drive File",
            "telegram_message_id": row["telegram_message_id"],
            "file_name": row["name"] if "name" in row.keys() else row["file_name"],
            "file_size": row["size"] if "size" in row.keys() else row["file_size"],
            "mime_type": row["mime_type"] if "mime_type" in row.keys() else None,
            "folder": id_map.get(str(folder_id)) if folder_id else None,
            "uploaded_by_label": row["uploaded_by"] if "uploaded_by" in row.keys() else None,
            "created_at": row["created_at"] if "created_at" in row.keys() else now_datetime(),
        }).insert(ignore_permissions=True)
    return len(rows)


def _portal_users(conn):
    rows = _table(conn, "portal_users")
    for row in rows:
        username = row["username"]
        if not frappe.db.exists("Telegram Drive Portal User", username):
            frappe.get_doc({"doctype": "Telegram Drive Portal User", "username": username, "password_hash": row["password_hash"], "can_upload": row["can_upload"] if "can_upload" in row.keys() else 0, "enabled": row["enabled"] if "enabled" in row.keys() else 1, "created_at": row["created_at"] if "created_at" in row.keys() else now_datetime()}).insert(ignore_permissions=True)
    return len(rows)


def _shares(conn):
    rows = _table(conn, "file_shares")
    for row in rows:
        token = row["token"]
        message_id = row["telegram_message_id"] if "telegram_message_id" in row.keys() else None
        drive_file = row["file_id"] if "file_id" in row.keys() and frappe.db.exists("Telegram Drive File", row["file_id"]) else None
        if not drive_file and message_id:
            drive_file = frappe.db.get_value("Telegram Drive File", {"telegram_message_id": message_id}, "name")
        if drive_file and not frappe.db.exists("Telegram Drive Share", token):
            frappe.get_doc({"doctype": "Telegram Drive Share", "token": token, "drive_file": drive_file, "enabled": 1, "created_at": row["created_at"] if "created_at" in row.keys() else now_datetime()}).insert(ignore_permissions=True)
    return len(rows)


def _settings(conn):
    rows = _table(conn, "app_settings")
    doc = frappe.get_single("Telegram Drive Setting")
    for row in rows:
        key = row["key"] if "key" in row.keys() else row["setting_key"]
        value = row["value"] if "value" in row.keys() else row["setting_value"]
        if key == "drive_name":
            doc.drive_name = value
    doc.save(ignore_permissions=True)


def _notes(conn):
    rows = _table(conn, "cloud_notes")
    for row in rows:
        frappe.get_doc({"doctype": "Telegram Drive Cloud Note", "title": row["title"], "body": row["body"], "color": row["color"] if "color" in row.keys() else "yellow", "created_by_label": row["created_by"] if "created_by" in row.keys() else None, "created_at": row["created_at"] if "created_at" in row.keys() else now_datetime(), "updated_at": row["updated_at"] if "updated_at" in row.keys() else now_datetime()}).insert(ignore_permissions=True)
    return len(rows)
