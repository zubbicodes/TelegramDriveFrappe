import mimetypes
import os
import time

import frappe
from frappe.utils import now_datetime

from telegram_drive.services import progress, telegram_service
from telegram_drive.services.activity import log_file_activity
from telegram_drive.services.security import current_actor_label, make_token, require_admin, require_drive_access, require_drive_permission
from telegram_drive.services.temp_files import safe_temp_path


def _file(doc):
    return {"id": doc.name, "name": doc.file_name, "size": doc.file_size, "mime_type": doc.mime_type, "folder_id": doc.folder, "telegram_message_id": doc.telegram_message_id, "uploaded_by": doc.uploaded_by_label, "uploaded_by_label": doc.uploaded_by_label, "created_at": doc.created_at}


@frappe.whitelist()
def list(folder_id=None, search=None):
    require_drive_access()
    filters = {}
    if folder_id:
        filters["folder"] = folder_id
    else:
        filters["folder"] = ["is", "not set"]
    if search:
        filters["file_name"] = ["like", f"%{search}%"]
    return [_file(d) for d in frappe.get_all("Telegram Drive File", filters=filters, fields=["name", "file_name", "file_size", "mime_type", "folder", "telegram_message_id", "uploaded_by_label", "created_at"], order_by="created_at desc")]


def _save_upload_file(fieldname="file"):
    uploaded = frappe.request.files.get(fieldname) or frappe.request.files.get("chunk")
    if not uploaded:
        frappe.throw("No file uploaded")
    path = safe_temp_path(f"{make_token(12)}-{uploaded.filename}")
    uploaded.save(path)
    return path, uploaded.filename, uploaded.mimetype or mimetypes.guess_type(uploaded.filename)[0]


@frappe.whitelist()
def upload(folder_id=None):
    require_drive_permission("can_upload")
    return _upload(folder_id, current_actor_label())


def _upload(folder_id=None, uploaded_by_label=None):
    path, filename, mime_type = _save_upload_file()
    upload_id = frappe.form_dict.get("upload_id") or make_token(16)
    progress.set_progress("upload", upload_id, progress.initial("Receiving file"))
    frappe.enqueue("telegram_drive.api.files.finish_upload", queue="long", upload_id=upload_id, path=path, filename=filename, mime_type=mime_type, folder_id=folder_id, uploaded_by_label=uploaded_by_label)
    return {"upload_id": upload_id}


@frappe.whitelist()
def upload_chunk(upload_id, filename, chunk_index, total_chunks, total_size=None, mime_type=None, folder_id=None):
    require_drive_permission("can_upload")
    return _upload_chunk(upload_id, filename, chunk_index, total_chunks, folder_id, current_actor_label(), total_size, mime_type)


def _upload_chunk(upload_id, filename, chunk_index, total_chunks, folder_id=None, uploaded_by_label=None, total_size=None, mime_type=None):
    uploaded = frappe.request.files.get("chunk") or frappe.request.files.get("file")
    if not uploaded:
        frappe.throw("No chunk uploaded")
    path = safe_temp_path(f"{upload_id}-{filename}")
    mode = "ab" if int(chunk_index) else "wb"
    with open(path, mode) as handle:
        handle.write(uploaded.read())
    bytes_done = os.path.getsize(path)
    percent = min(10, int((bytes_done / int(total_size)) * 10)) if total_size else int(((int(chunk_index) + 1) / int(total_chunks)) * 10)
    progress.update_progress("upload", upload_id, percent=percent, stage="Receiving file", bytes_done=bytes_done, bytes_total=int(total_size) if total_size else None)
    if int(chunk_index) + 1 >= int(total_chunks):
        if total_size and bytes_done != int(total_size):
            frappe.throw("Uploaded size does not match expected size")
        progress.update_progress("upload", upload_id, percent=10, stage="Queued for Telegram", bytes_done=bytes_done, bytes_total=int(total_size) if total_size else bytes_done)
        frappe.enqueue("telegram_drive.api.files.finish_upload", queue="long", upload_id=upload_id, path=path, filename=filename, mime_type=mime_type or mimetypes.guess_type(filename)[0], folder_id=folder_id, uploaded_by_label=uploaded_by_label)
        return {"status": "processing", "upload_id": upload_id}
    return {"status": "chunk_received", "upload_id": upload_id, "bytes_done": bytes_done}


def finish_upload(upload_id, path, filename, mime_type=None, folder_id=None, uploaded_by_label=None):
    started = time.time()

    def cb(done, total):
        elapsed = max(time.time() - started, 0.001)
        progress.update_progress("upload", upload_id, percent=int(done * 100 / total) if total else 0, stage="Uploading to Telegram", bytes_done=done, bytes_total=total, speed_bps=int(done / elapsed))

    try:
        message_id = telegram_service.upload_file(path, cb)
        doc = frappe.get_doc({"doctype": "Telegram Drive File", "telegram_message_id": message_id, "file_name": filename, "file_size": os.path.getsize(path), "mime_type": mime_type, "folder": folder_id, "uploaded_by_label": uploaded_by_label, "created_at": now_datetime()})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        log_file_activity("Upload", doc, uploaded_by_label)
        progress.update_progress("upload", upload_id, percent=100, stage="Done", done=True, file_id=doc.name)
    except Exception as exc:
        progress.update_progress("upload", upload_id, stage="Failed", done=True, error=str(exc))
        raise
    finally:
        if os.path.exists(path):
            os.remove(path)


@frappe.whitelist()
def start_download(file_id):
    require_drive_permission("can_download")
    return _start_download(file_id, actor=current_actor_label(), context="frappe queued download")


def _start_download(file_id, actor=None, context=None):
    download_id = make_token(16)
    progress.set_progress("download", download_id, {**progress.initial("Preparing"), "temp_path": None, "filename": None})
    frappe.enqueue("telegram_drive.api.files.finish_download", queue="long", download_id=download_id, file_id=file_id, actor=actor or frappe.session.user, context=context)
    return {"download_id": download_id}


def finish_download(download_id, file_id, actor=None, context=None):
    doc = frappe.get_doc("Telegram Drive File", file_id)
    path = safe_temp_path(f"{download_id}-{doc.file_name}")
    started = time.time()

    def cb(done, total):
        elapsed = max(time.time() - started, 0.001)
        progress.update_progress("download", download_id, percent=int(done * 100 / total) if total else 0, stage="Downloading from Telegram", bytes_done=done, bytes_total=total, speed_bps=int(done / elapsed), filename=doc.file_name)

    try:
        telegram_service.download_file(doc.telegram_message_id, path, cb)
        progress.update_progress("download", download_id, percent=100, stage="Complete", done=True, temp_path=path, filename=doc.file_name)
        log_file_activity("Download", doc, actor, context)
    except Exception as exc:
        progress.update_progress("download", download_id, stage="Failed", done=True, error=str(exc))
        raise


@frappe.whitelist()
def temp_download(download_id):
    require_drive_permission("can_download")
    return _temp_download(download_id)


def _temp_download(download_id):
    payload = progress.get_progress("download", download_id)
    path = payload.get("temp_path")
    if not path or not os.path.exists(path):
        frappe.throw("Download is not ready")
    frappe.local.response.filename = payload.get("filename") or os.path.basename(path)
    with open(path, "rb") as handle:
        frappe.local.response.filecontent = handle.read()
    frappe.local.response.type = "download"
    os.remove(path)
    progress.update_progress("download", download_id, temp_path=None, stage="Downloaded to computer")


@frappe.whitelist()
def download(file_id):
    require_drive_permission("can_download")
    actor = current_actor_label()
    download_id = _start_download(file_id, actor=actor, context="frappe direct download")["download_id"]
    finish_download(download_id, file_id, actor=actor, context="frappe direct download")
    return temp_download(download_id)


@frappe.whitelist()
def create_share_link(file_id):
    require_drive_permission("can_share")
    return _create_share_link(file_id)


def _create_share_link(file_id):
    token = make_token(32)
    doc = frappe.get_doc({"doctype": "Telegram Drive Share", "token": token, "drive_file": file_id, "enabled": 1, "created_at": now_datetime(), "download_count": 0})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"token": token, "url": f"/api/method/telegram_drive.api.files.public_share_download?token={token}"}


@frappe.whitelist(allow_guest=True)
def public_share_download(token):
    share = frappe.get_doc("Telegram Drive Share", token)
    if not share.enabled:
        frappe.throw("Share disabled")
    share.download_count = (share.download_count or 0) + 1
    share.save(ignore_permissions=True)
    frappe.db.commit()
    doc = frappe.get_doc("Telegram Drive File", share.drive_file)
    path = safe_temp_path(f"share-{make_token(8)}-{doc.file_name}")
    telegram_service.download_file(doc.telegram_message_id, path)
    log_file_activity("Download", doc, "Public Share", f"share token {token}")
    frappe.local.response.filename = doc.file_name
    frappe.local.response.filecontent = open(path, "rb").read()
    frappe.local.response.type = "download"


@frappe.whitelist()
def delete(file_id):
    require_drive_permission("can_delete")
    doc = frappe.get_doc("Telegram Drive File", file_id)
    try:
        telegram_service.delete_message(doc.telegram_message_id)
    finally:
        log_file_activity("Delete", doc, current_actor_label(), "file deleted from drive")
        frappe.delete_doc("Telegram Drive File", file_id, ignore_permissions=True)
        frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def move(file_id, folder_id=None):
    require_drive_permission("can_move")
    doc = frappe.get_doc("Telegram Drive File", file_id)
    doc.folder = folder_id
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return _file(doc)
