import frappe
from frappe.utils import now_datetime

from telegram_drive.services.security import current_actor_label, require_drive_access, require_drive_permission


def _row(doc):
    return {"id": doc.name, "name": doc.folder_name, "parent_id": doc.parent_folder, "created_at": doc.created_at}


@frappe.whitelist()
def list(parent_id=None):
    require_drive_access()
    filters = {"parent_folder": parent_id or ["is", "not set"]}
    return [_row(d) for d in frappe.get_all("Telegram Drive Folder", filters=filters, fields=["name", "folder_name", "parent_folder", "created_at"])]


@frappe.whitelist()
def list_all():
    require_drive_access()
    return [_row(d) for d in frappe.get_all("Telegram Drive Folder", fields=["name", "folder_name", "parent_folder", "created_at"])]


@frappe.whitelist()
def create(folder_name=None, name=None, parent_id=None, created_by_label=None):
    require_drive_permission("can_manage_folders")
    folder_name = folder_name or name
    doc = frappe.get_doc({"doctype": "Telegram Drive Folder", "folder_name": folder_name, "parent_folder": parent_id, "created_at": now_datetime(), "created_by_label": created_by_label or current_actor_label()})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return _row(doc)


def _descendants(folder):
    children = frappe.get_all("Telegram Drive Folder", filters={"parent_folder": folder}, pluck="name")
    out = []
    for child in children:
        out.append(child)
        out.extend(_descendants(child))
    return out


@frappe.whitelist()
def delete(folder_id):
    require_drive_permission("can_manage_folders")
    folders = list(reversed(_descendants(folder_id))) + [folder_id]
    for folder in folders:
        if frappe.db.exists("Telegram Drive File", {"folder": folder}):
            frappe.throw("Folder contains files. Delete or move files first.")
        frappe.delete_doc("Telegram Drive Folder", folder, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}
