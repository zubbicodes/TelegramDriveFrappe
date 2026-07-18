import os

import frappe

from telegram_drive.services import progress
from telegram_drive.services.security import require_admin, require_drive_access
from telegram_drive.services.temp_files import cleanup_old, list_temp, safe_temp_path


@frappe.whitelist()
def upload_progress(upload_id):
    require_drive_access()
    return progress.get_progress("upload", upload_id)


@frappe.whitelist()
def download_progress(download_id):
    require_drive_access()
    return progress.get_progress("download", download_id)


@frappe.whitelist()
def list_temp_files():
    require_admin()
    cleanup_old()
    return list_temp()


@frappe.whitelist()
def delete_temp_file(filename):
    require_admin()
    path = safe_temp_path(filename)
    if os.path.exists(path):
        os.remove(path)
    return {"ok": True}
