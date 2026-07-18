import frappe
from frappe.utils import add_days, now_datetime

from telegram_drive.api import files as file_api
from telegram_drive.api import folders as folder_api
from telegram_drive.api import notes as notes_api
from telegram_drive.services.security import check_portal_password, get_portal_user, make_token, require_admin, set_portal_password


def _user(doc):
    return {"id": doc.name, "username": doc.username, "can_upload": bool(doc.can_upload), "enabled": bool(doc.enabled), "created_at": doc.created_at, "last_login": doc.last_login}


@frappe.whitelist(allow_guest=True)
def login(username, password):
    if not frappe.db.exists("Telegram Drive Portal User", username):
        frappe.throw("Invalid login", frappe.AuthenticationError)
    doc = frappe.get_doc("Telegram Drive Portal User", username)
    if not doc.enabled or not check_portal_password(username, password):
        frappe.throw("Invalid login", frappe.AuthenticationError)
    token = make_token(32)
    frappe.get_doc({"doctype": "Telegram Drive Portal Session", "token": token, "portal_user": username, "created_at": now_datetime(), "expires_at": add_days(now_datetime(), 30)}).insert(ignore_permissions=True)
    doc.last_login = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"token": token, "user": _user(doc)}


@frappe.whitelist(allow_guest=True)
def me():
    return {"user": _user(get_portal_user())}


@frappe.whitelist(allow_guest=True)
def change_password(old_password=None, current_password=None, new_password=None):
    user = get_portal_user()
    old_password = old_password or current_password
    if not check_portal_password(user.name, old_password):
        frappe.throw("Invalid password", frappe.AuthenticationError)
    set_portal_password(user.name, new_password)
    return {"ok": True}


@frappe.whitelist()
def list_users():
    require_admin()
    return [_user(d) for d in frappe.get_all("Telegram Drive Portal User", fields=["name", "username", "can_upload", "enabled", "created_at", "last_login"])]


@frappe.whitelist()
def create_user(username, password, can_upload=0, enabled=1):
    require_admin()
    doc = frappe.get_doc({"doctype": "Telegram Drive Portal User", "username": username, "password_hash": "pending", "can_upload": int(can_upload), "enabled": int(enabled), "created_at": now_datetime()})
    doc.insert(ignore_permissions=True)
    set_portal_password(username, password)
    frappe.db.commit()
    return _user(frappe.get_doc("Telegram Drive Portal User", username))


@frappe.whitelist()
def update_user(username, password=None, can_upload=None, enabled=None):
    require_admin()
    doc = frappe.get_doc("Telegram Drive Portal User", username)
    if can_upload is not None:
        doc.can_upload = int(can_upload)
    if enabled is not None:
        doc.enabled = int(enabled)
    doc.save(ignore_permissions=True)
    if password:
        set_portal_password(username, password)
    frappe.db.commit()
    return _user(doc)


@frappe.whitelist()
def delete_user(username):
    require_admin()
    frappe.delete_doc("Telegram Drive Portal User", username, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist(allow_guest=True)
def list_folders(parent_id=None):
    get_portal_user()
    filters = {"parent_folder": parent_id or ["is", "not set"]}
    return [{"id": d.name, "name": d.folder_name, "parent_id": d.parent_folder, "created_at": d.created_at} for d in frappe.get_all("Telegram Drive Folder", filters=filters, fields=["name", "folder_name", "parent_folder", "created_at"])]


@frappe.whitelist(allow_guest=True)
def create_folder(folder_name, parent_id=None):
    user = get_portal_user()
    if not user.can_upload:
        frappe.throw("Upload permission required", frappe.PermissionError)
    doc = frappe.get_doc({"doctype": "Telegram Drive Folder", "folder_name": folder_name, "parent_folder": parent_id, "created_at": now_datetime(), "created_by_label": user.username})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"id": doc.name, "name": doc.folder_name, "parent_id": doc.parent_folder, "created_at": doc.created_at}


@frappe.whitelist(allow_guest=True)
def list_files(folder_id=None, search=None):
    get_portal_user()
    filters = {"folder": folder_id or ["is", "not set"]}
    if search:
        filters["file_name"] = ["like", f"%{search}%"]
    return [file_api._file(d) for d in frappe.get_all("Telegram Drive File", filters=filters, fields=["name", "file_name", "file_size", "mime_type", "folder", "telegram_message_id", "uploaded_by_label", "created_at"], order_by="created_at desc")]


@frappe.whitelist(allow_guest=True)
def upload(folder_id=None):
    user = get_portal_user()
    if not user.can_upload:
        frappe.throw("Upload permission required", frappe.PermissionError)
    return file_api._upload(folder_id=folder_id, uploaded_by_label=user.username)


@frappe.whitelist(allow_guest=True)
def upload_chunk(upload_id, filename, chunk_index, total_chunks, total_size=None, mime_type=None, folder_id=None):
    user = get_portal_user()
    if not user.can_upload:
        frappe.throw("Upload permission required", frappe.PermissionError)
    return file_api._upload_chunk(upload_id, filename, chunk_index, total_chunks, folder_id, user.username, total_size, mime_type)


@frappe.whitelist(allow_guest=True)
def create_share_link(file_id):
    get_portal_user()
    return file_api._create_share_link(file_id)


@frappe.whitelist(allow_guest=True)
def upload_progress(upload_id):
    get_portal_user()
    return file_api.progress.get_progress("upload", upload_id)


@frappe.whitelist(allow_guest=True)
def download_progress(download_id):
    get_portal_user()
    return file_api.progress.get_progress("download", download_id)


@frappe.whitelist(allow_guest=True)
def start_download(file_id):
    user = get_portal_user()
    return file_api._start_download(file_id, actor=user.username, context="portal queued download")


@frappe.whitelist(allow_guest=True)
def temp_download(download_id):
    get_portal_user()
    return file_api._temp_download(download_id)


@frappe.whitelist(allow_guest=True)
def download(file_id):
    user = get_portal_user()
    download_id = file_api._start_download(file_id, actor=user.username, context="portal direct download")["download_id"]
    file_api.finish_download(download_id, file_id, actor=user.username, context="portal direct download")
    return file_api._temp_download(download_id)


@frappe.whitelist(allow_guest=True)
def get_settings():
    get_portal_user()
    from telegram_drive.api.settings import _get_settings
    return _get_settings()


@frappe.whitelist(allow_guest=True)
def storage_summary():
    get_portal_user()
    from telegram_drive.api.settings import _storage_summary
    return _storage_summary()


@frappe.whitelist(allow_guest=True)
def list_notes():
    get_portal_user()
    return [{"id": d.name, "title": d.title, "body": d.body, "color": d.color, "created_by_label": d.created_by_label, "created_at": d.created_at, "updated_at": d.updated_at} for d in frappe.get_all("Telegram Drive Cloud Note", fields=["name", "title", "body", "color", "created_by_label", "created_at", "updated_at"], order_by="modified desc")]


@frappe.whitelist(allow_guest=True)
def create_note(title, body="", color="yellow"):
    user = get_portal_user()
    doc = frappe.get_doc({"doctype": "Telegram Drive Cloud Note", "title": title, "body": body, "color": color, "created_by_label": user.username, "created_at": now_datetime(), "updated_at": now_datetime()})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return notes_api._note(doc)


@frappe.whitelist(allow_guest=True)
def update_note(note_id, title=None, body=None, color=None):
    get_portal_user()
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
    return notes_api._note(doc)


@frappe.whitelist(allow_guest=True)
def delete_note(note_id):
    get_portal_user()
    frappe.delete_doc("Telegram Drive Cloud Note", note_id, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}
