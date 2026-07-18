import frappe


def has_app_permission():
    roles = set(frappe.get_roles())
    return bool({"Telegram Drive Admin", "Telegram Drive User"} & roles)
