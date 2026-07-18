import secrets

import frappe
from frappe.utils.password import check_password, update_password


ADMIN_ROLE = "Telegram Drive Admin"
USER_ROLE = "Telegram Drive User"
SYSTEM_MANAGER_ROLE = "System Manager"
ACCESS_ROLES = {ADMIN_ROLE, USER_ROLE}
DEFAULT_USER_PERMISSIONS = {
    "can_upload": False,
    "can_download": True,
    "can_delete": False,
    "can_manage_folders": False,
    "can_share": False,
    "can_move": False,
}


def has_drive_role():
    if frappe.session.user == "Guest":
        return False
    roles = set(frappe.get_roles())
    return frappe.session.user == "Administrator" or SYSTEM_MANAGER_ROLE in roles or bool(ACCESS_ROLES & roles)


def has_admin_role():
    if frappe.session.user == "Guest":
        return False
    roles = set(frappe.get_roles())
    return frappe.session.user == "Administrator" or SYSTEM_MANAGER_ROLE in roles or ADMIN_ROLE in roles


def require_drive_access():
    if get_owner_token_doc():
        return
    if not has_drive_role():
        frappe.throw("Telegram Drive access required", frappe.PermissionError)


def require_admin():
    if get_owner_token_doc():
        return
    if not has_admin_role():
        frappe.throw("Telegram Drive Admin role required", frappe.PermissionError)


def current_actor_label(default=None):
    if frappe.session.user != "Guest":
        return frappe.session.user
    owner = get_owner_token_doc()
    if owner:
        return owner.phone
    return default or "Guest"


def get_current_drive_permissions():
    if get_owner_token_doc() or has_admin_role():
        return {
            "can_admin": True,
            "can_upload": True,
            "can_download": True,
            "can_delete": True,
            "can_manage_folders": True,
            "can_share": True,
            "can_move": True,
        }
    require_drive_access()
    values = frappe.db.get_value(
        "Telegram Drive User Permission",
        {"user": frappe.session.user, "enabled": 1},
        ["can_upload", "can_download", "can_delete", "can_manage_folders", "can_share", "can_move"],
        as_dict=True,
    )
    permissions = dict(DEFAULT_USER_PERMISSIONS)
    if values:
        permissions.update({key: bool(values.get(key)) for key in permissions})
    permissions["can_admin"] = False
    return permissions


def require_drive_permission(permission):
    permissions = get_current_drive_permissions()
    if not permissions.get(permission):
        frappe.throw("Telegram Drive permission required", frappe.PermissionError)
    return permissions


def make_token(bytes_count=32):
    return secrets.token_urlsafe(bytes_count)


def set_portal_password(username, password):
    update_password(username, password, doctype="Telegram Drive Portal User", fieldname="password_hash")


def check_portal_password(username, password):
    return check_password("Telegram Drive Portal User", username, password, fieldname="password_hash")


def get_bearer_token():
    try:
        header = frappe.get_request_header("Authorization") or ""
    except RuntimeError:
        header = ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return frappe.form_dict.get("portal_token") or frappe.form_dict.get("token")


def get_header_token(name):
    try:
        header_value = frappe.get_request_header(name)
    except RuntimeError:
        header_value = None
    return header_value or frappe.form_dict.get("token")


def get_owner_token_doc():
    token = get_header_token("X-Token")
    if not token:
        return None
    name = frappe.db.get_value("Telegram Drive Owner", {"token": token}, "name")
    if not name:
        return None
    doc = frappe.get_doc("Telegram Drive Owner", name)
    if not doc.is_authorized:
        frappe.throw("Not authorized", frappe.PermissionError)
    return doc


def get_portal_user():
    token = frappe.get_request_header("X-Portal-Token") or get_bearer_token()
    if not token:
        frappe.throw("Portal token required", frappe.PermissionError)
    session = frappe.db.get_value(
        "Telegram Drive Portal Session",
        {"token": token},
        ["portal_user", "expires_at"],
        as_dict=True,
    )
    if not session:
        frappe.throw("Invalid portal token", frappe.PermissionError)
    if session.expires_at and session.expires_at < frappe.utils.now_datetime():
        frappe.throw("Portal token expired", frappe.PermissionError)
    user = frappe.get_doc("Telegram Drive Portal User", session.portal_user)
    if not user.enabled:
        frappe.throw("Portal user disabled", frappe.PermissionError)
    return user
