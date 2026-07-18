import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def after_install():
    ensure_roles()

    for parts in (("private", "telegram_drive", "sessions"), ("private", "telegram_drive", "temp")):
        frappe.create_folder(frappe.get_site_path(*parts))

    ensure_settings()

    ensure_workspace()
    ensure_activity_log_permission()
    ensure_activity_log_status_options()


def ensure_roles():
    for old_role, new_role in (("Telegram Drive Admin", "FlowDrive Admin"), ("Telegram Drive User", "FlowDrive User")):
        if frappe.db.exists("Role", old_role) and not frappe.db.exists("Role", new_role):
            frappe.rename_doc("Role", old_role, new_role, force=True)

    for role in ("FlowDrive Admin", "FlowDrive User"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)


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
    ensure_roles()
    if frappe.db.exists("Workspace", "Telegram Drive") and not frappe.db.exists("Workspace", "FlowDrive"):
        frappe.rename_doc("Workspace", "Telegram Drive", "FlowDrive", force=True)

    if not frappe.db.exists("Workspace", "FlowDrive"):
        workspace = frappe.get_doc(
            {
                "doctype": "Workspace",
                "label": "FlowDrive",
                "title": "FlowDrive",
                "module": "Telegram Drive",
                "public": 1,
                "icon": "cloud",
                "type": "URL",
                "external_link": "/telegram-drive",
                "content": "[]",
                "sequence_id": 25,
            }
        )
        workspace.append("roles", {"role": "FlowDrive Admin"})
        workspace.append("roles", {"role": "FlowDrive User"})
        workspace.insert(ignore_permissions=True)
    else:
        workspace = frappe.get_doc("Workspace", "FlowDrive")
        workspace.label = "FlowDrive"
        workspace.title = "FlowDrive"
        workspace.module = "Telegram Drive"
        workspace.public = 1
        workspace.icon = "cloud"
        workspace.type = "URL"
        workspace.external_link = "/telegram-drive"
        existing_roles = {row.role for row in workspace.roles}
        for role in ("FlowDrive Admin", "FlowDrive User"):
            if role not in existing_roles:
                workspace.append("roles", {"role": role})
        workspace.save(ignore_permissions=True)

    frappe.db.commit()


def ensure_activity_log_permission():
    if not frappe.db.exists("DocPerm", {"parent": "Activity Log", "role": "FlowDrive Admin"}):
        perm = frappe.new_doc("DocPerm")
        perm.parent = "Activity Log"
        perm.parenttype = "DocType"
        perm.parentfield = "permissions"
        perm.role = "FlowDrive Admin"
        perm.read = 1
        perm.export = 1
        perm.insert(ignore_permissions=True)
    frappe.db.commit()


def ensure_activity_log_status_options():
    options = "\nSuccess\nFailed\nLinked\nClosed\nUpload\nDownload\nDelete"
    make_property_setter("Activity Log", "status", "options", options, "Text", validate_fields_for_doctype=False)
    frappe.db.commit()
