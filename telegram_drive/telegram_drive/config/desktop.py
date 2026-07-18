from frappe import _


def get_data():
    return [
        {
            "module_name": "Telegram Drive",
            "category": "Modules",
            "label": _("FlowDrive"),
            "color": "blue",
            "icon": "octicon octicon-cloud",
            "type": "module",
            "description": "Secure cloud drive",
        }
    ]
