from frappe import _


def get_data():
    return [
        {
            "module_name": "Telegram Drive",
            "category": "Modules",
            "label": _("Telegram Drive"),
            "color": "blue",
            "icon": "octicon octicon-cloud",
            "type": "module",
            "description": "Telegram Saved Messages backed drive",
        }
    ]
