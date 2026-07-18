import asyncio

import frappe
from telethon.errors import SessionPasswordNeededError

from telegram_drive.services import telegram_service
from telegram_drive.services.security import get_owner_token_doc, has_admin_role, has_drive_role, make_token, require_admin, require_drive_access


@frappe.whitelist(allow_guest=True)
def csrf():
    return {"csrf_token": frappe.session.data.csrf_token}


@frappe.whitelist()
def start(phone, api_id, api_hash, proxy_type="none", proxy_host=None, proxy_port=None, proxy_secret=None, proxy_username=None, proxy_password=None):
    require_admin()
    doc = frappe.get_doc("Telegram Drive Owner", phone) if frappe.db.exists("Telegram Drive Owner", phone) else frappe.new_doc("Telegram Drive Owner")
    token = doc.token or make_token(24)
    doc.update({
        "phone": phone,
        "token": token,
        "api_id": int(api_id),
        "api_hash": api_hash,
        "session_name": f"telegram_drive_{phone.replace('+', '').replace(' ', '')}",
        "proxy_type": proxy_type or "none",
        "proxy_host": proxy_host,
        "proxy_port": proxy_port,
        "proxy_secret": proxy_secret,
        "proxy_username": proxy_username,
        "proxy_password": proxy_password,
    })
    if doc.is_authorized:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "already_authorized", "token": token}
    try:
        doc.phone_code_hash = telegram_service.send_code(doc)
    except ValueError as exc:
        frappe.throw(str(exc))
    except TimeoutError:
        frappe.throw("Timed out while contacting Telegram. Check the proxy settings and try again.")
    except asyncio.TimeoutError:
        frappe.throw("Timed out while contacting Telegram. Check the proxy settings and try again.")
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "code_sent", "token": token}


@frappe.whitelist()
def verify_code(token=None, phone=None, code=None):
    require_admin()
    owner = frappe.get_doc("Telegram Drive Owner", phone) if phone else frappe.get_doc("Telegram Drive Owner", frappe.db.get_value("Telegram Drive Owner", {"token": token}, "name"))
    try:
        authorized = telegram_service.sign_in_code(owner, code)
    except SessionPasswordNeededError:
        return {"status": "password_needed"}
    owner.is_authorized = 1 if authorized else 0
    owner.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success" if authorized else "failed"}


@frappe.whitelist()
def verify_password(token=None, phone=None, password=None):
    require_admin()
    owner = frappe.get_doc("Telegram Drive Owner", phone) if phone else frappe.get_doc("Telegram Drive Owner", frappe.db.get_value("Telegram Drive Owner", {"token": token}, "name"))
    authorized = telegram_service.sign_in_password(owner, password)
    owner.is_authorized = 1 if authorized else 0
    owner.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success" if authorized else "failed"}


@frappe.whitelist(allow_guest=True)
def me():
    require_drive_access()
    owner = frappe.db.get_value("Telegram Drive Owner", {"is_authorized": 1}, ["phone", "is_authorized"], as_dict=True)
    owner_token = get_owner_token_doc()
    desk_theme = "Light"
    if frappe.session.user != "Guest":
        desk_theme = frappe.get_cached_value("User", frappe.session.user, "desk_theme") or "Light"
    return {
        "phone": owner.phone if owner else None,
        "authorized": bool(owner),
        "frappe_user": frappe.session.user if frappe.session.user != "Guest" and has_drive_role() else None,
        "can_admin": bool(owner_token or has_admin_role()),
        "desk_theme": desk_theme,
    }
