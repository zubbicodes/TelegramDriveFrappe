import frappe

from telegram_drive.services.security import get_current_drive_permissions, require_admin, require_drive_access


PERMISSION_FIELDS = ("can_upload", "can_download", "can_delete", "can_manage_folders", "can_share", "can_move")


def _row(doc):
    return {
        "id": doc.name,
        "user": doc.user,
        "enabled": bool(doc.enabled),
        **{field: bool(doc.get(field)) for field in PERMISSION_FIELDS},
    }


@frappe.whitelist(allow_guest=True)
def me():
    require_drive_access()
    return get_current_drive_permissions()


@frappe.whitelist()
def list_users():
    require_admin()
    return [
        _row(d)
        for d in frappe.get_all(
            "Telegram Drive User Permission",
            fields=["name", "user", "enabled", *PERMISSION_FIELDS],
            order_by="user asc",
        )
    ]


@frappe.whitelist()
def save_user(user, enabled=1, **kwargs):
    require_admin()
    exists = frappe.db.exists("Telegram Drive User Permission", user)
    doc = frappe.get_doc("Telegram Drive User Permission", user) if exists else frappe.new_doc("Telegram Drive User Permission")
    doc.user = user
    doc.enabled = int(enabled)
    for field in PERMISSION_FIELDS:
        if field in kwargs:
            doc.set(field, int(kwargs[field]))
    doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return _row(doc)


@frappe.whitelist()
def delete_user(user):
    require_admin()
    if frappe.db.exists("Telegram Drive User Permission", user):
        frappe.delete_doc("Telegram Drive User Permission", user, ignore_permissions=True)
        frappe.db.commit()
    return {"ok": True}
