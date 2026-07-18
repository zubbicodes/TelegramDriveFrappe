import frappe


def has_app_permission():
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles())
    return bool({"Telegram Drive Admin", "Telegram Drive User"} & roles)
