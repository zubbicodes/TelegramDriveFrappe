import frappe

from telegram_drive.services.security import require_admin, require_drive_access


@frappe.whitelist()
def get_settings():
    require_drive_access()
    return _get_settings()


def _get_settings():
    doc = frappe.get_single("Telegram Drive Setting")
    return {k: doc.get(k) for k in ("drive_name", "temp_retention_hours", "chunk_size_mb", "large_upload_threshold_mb")}


@frappe.whitelist()
def update_settings(**kwargs):
    require_admin()
    doc = frappe.get_single("Telegram Drive Setting")
    for field in ("drive_name", "temp_retention_hours", "chunk_size_mb", "large_upload_threshold_mb"):
        if field in kwargs:
            doc.set(field, kwargs[field])
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _get_settings()


@frappe.whitelist()
def storage_summary(folder_id=None):
    require_drive_access()
    return _storage_summary(folder_id)


def _storage_summary(folder_id=None):
    drive_name = frappe.db.get_single_value("Telegram Drive Setting", "drive_name") or "My Drive"
    folders = frappe.get_all("Telegram Drive Folder", fields=["name", "folder_name", "parent_folder"])
    files = frappe.get_all("Telegram Drive File", fields=["name", "file_size", "folder"])
    children = {}
    names = {}
    for folder in folders:
        children.setdefault(folder.parent_folder, []).append(folder.name)
        names[folder.name] = folder.folder_name
    direct = {}
    for file in files:
        direct[file.folder] = direct.get(file.folder, 0) + (file.file_size or 0)
    totals = {}

    def folder_total(name):
        if name in totals:
            return totals[name]
        total = direct.get(name, 0)
        for child in children.get(name, []):
            total += folder_total(child)
        totals[name] = total
        return total

    drive_size = direct.get(None, 0) + sum(folder_total(root) for root in children.get(None, []))
    current_size = folder_total(folder_id) if folder_id else drive_size
    return {
        "drive_name": drive_name,
        "drive_size": drive_size,
        "current_folder_id": folder_id,
        "current_name": names.get(folder_id, drive_name),
        "current_size": current_size,
        "folder_sizes": totals,
    }
