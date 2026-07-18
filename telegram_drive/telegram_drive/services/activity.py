import frappe
from frappe.utils import now_datetime


def actor_label(fallback=None):
    if fallback and fallback != "Guest":
        return fallback
    if frappe.session and frappe.session.user and frappe.session.user != "Guest":
        return frappe.session.user
    return fallback or "Guest"


def log_file_activity(action, drive_file=None, actor=None, context=None):
    actor = actor_label(actor)
    filename = getattr(drive_file, "file_name", None) or "Unknown file"
    subject = f"Telegram Drive {action}: {filename}"
    verbs = {"Upload": "uploaded", "Download": "downloaded", "Delete": "deleted"}
    content = f"{actor} {verbs.get(action, action.lower())} {filename}"
    if context:
        content = f"{content} ({context})"
    user = actor if frappe.db.exists("User", actor) else None
    if not user and frappe.session and frappe.session.user and frappe.session.user != "Guest":
        user = frappe.session.user

    doc = {
        "doctype": "Activity Log",
        "subject": subject,
        "content": content,
        "user": user,
        "full_name": actor,
        "operation": "",
        "status": "Success",
        "communication_date": now_datetime(),
    }
    if drive_file and frappe.db.exists("Telegram Drive File", drive_file.name):
        doc.update({"reference_doctype": "Telegram Drive File", "reference_name": drive_file.name})

    try:
        activity = frappe.get_doc(doc).insert(ignore_permissions=True)
        frappe.db.set_value("Activity Log", activity.name, "status", action, update_modified=False)
        frappe.db.commit()
    except Exception:
        try:
            doc.pop("reference_doctype", None)
            doc.pop("reference_name", None)
            activity = frappe.get_doc(doc).insert(ignore_permissions=True)
            frappe.db.set_value("Activity Log", activity.name, "status", action, update_modified=False)
            frappe.db.commit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Telegram Drive activity log failed: {action}")
