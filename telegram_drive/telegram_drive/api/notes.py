import frappe
from frappe.utils import now_datetime

from telegram_drive.services.security import current_actor_label, require_drive_access


def _note(doc):
    return {"id": doc.name, "title": doc.title, "body": doc.body, "color": doc.color, "created_by_label": doc.created_by_label, "created_at": doc.created_at, "updated_at": doc.updated_at}


@frappe.whitelist()
def list():
    require_drive_access()
    return [_note(d) for d in frappe.get_all("Telegram Drive Cloud Note", fields=["name", "title", "body", "color", "created_by_label", "created_at", "updated_at"], order_by="modified desc")]


@frappe.whitelist()
def create(title, body="", color="yellow"):
    require_drive_access()
    doc = frappe.get_doc({"doctype": "Telegram Drive Cloud Note", "title": title, "body": body, "color": color, "created_by_label": current_actor_label(), "created_at": now_datetime(), "updated_at": now_datetime()})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return _note(doc)


@frappe.whitelist()
def update(note_id, title=None, body=None, color=None):
    require_drive_access()
    doc = frappe.get_doc("Telegram Drive Cloud Note", note_id)
    if title is not None:
        doc.title = title
    if body is not None:
        doc.body = body
    if color is not None:
        doc.color = color
    doc.updated_at = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _note(doc)


@frappe.whitelist()
def delete(note_id):
    require_drive_access()
    frappe.delete_doc("Telegram Drive Cloud Note", note_id, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}
