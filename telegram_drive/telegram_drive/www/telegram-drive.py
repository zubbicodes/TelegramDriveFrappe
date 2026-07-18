import frappe


def get_context(context):
    theme = "Light"
    if frappe.session.user != "Guest":
        theme = frappe.get_cached_value("User", frappe.session.user, "desk_theme") or "Light"
    context.telegram_drive_theme = theme
