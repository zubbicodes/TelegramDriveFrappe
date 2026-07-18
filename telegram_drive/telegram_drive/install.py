import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_install():
    for role in ("Telegram Drive Admin", "Telegram Drive User"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)

    for parts in (("private", "telegram_drive", "sessions"), ("private", "telegram_drive", "temp")):
        frappe.create_folder(frappe.get_site_path(*parts))

    ensure_settings()

    ensure_workspace()
    ensure_activity_log_permission()
    ensure_activity_log_status_options()


def ensure_settings():
    doc = frappe.get_single("Telegram Drive Setting")
    changed = False
    defaults = {
        "drive_name": "My Drive",
        "temp_retention_hours": 6,
        "chunk_size_mb": 25,
        "large_upload_threshold_mb": 50,
    }
    for field, value in defaults.items():
        if not doc.get(field):
            doc.set(field, value)
            changed = True
    if changed:
        doc.save(ignore_permissions=True)
        frappe.db.commit()


def ensure_workspace():
    if not frappe.db.exists("Workspace", "Telegram Drive"):
        workspace = frappe.get_doc(
            {
                "doctype": "Workspace",
                "label": "Telegram Drive",
                "title": "Telegram Drive",
                "module": "Telegram Drive",
                "public": 1,
                "icon": "cloud",
                "type": "URL",
                "external_link": "/telegram-drive",
                "content": "[]",
                "sequence_id": 25,
            }
        )
        workspace.append("roles", {"role": "Telegram Drive Admin"})
        workspace.append("roles", {"role": "Telegram Drive User"})
        workspace.insert(ignore_permissions=True)
    else:
        workspace = frappe.get_doc("Workspace", "Telegram Drive")
        workspace.title = "Telegram Drive"
        workspace.module = "Telegram Drive"
        workspace.public = 1
        workspace.icon = "cloud"
        workspace.type = "URL"
        workspace.external_link = "/telegram-drive"
        existing_roles = {row.role for row in workspace.roles}
        for role in ("Telegram Drive Admin", "Telegram Drive User"):
            if role not in existing_roles:
                workspace.append("roles", {"role": role})
        workspace.save(ignore_permissions=True)

    frappe.db.commit()


def ensure_activity_log_permission():
    if not frappe.db.exists("DocPerm", {"parent": "Activity Log", "role": "Telegram Drive Admin"}):
        perm = frappe.new_doc("DocPerm")
        perm.parent = "Activity Log"
        perm.parenttype = "DocType"
        perm.parentfield = "permissions"
        perm.role = "Telegram Drive Admin"
        perm.read = 1
        perm.export = 1
        perm.insert(ignore_permissions=True)
    frappe.db.commit()


def ensure_activity_log_status_options():
    options = "\nSuccess\nFailed\nLinked\nClosed\nUpload\nDownload\nDelete"
    make_property_setter("Activity Log", "status", "options", options, "Text", validate_fields_for_doctype=False)
    frappe.db.commit()
