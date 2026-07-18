app_name = "telegram_drive"
app_title = "FlowDrive"
app_publisher = "FLOW"
app_description = "Secure cloud drive for Frappe/ERPNext"
app_email = "admin@example.com"
app_license = "MIT"

fixtures = [
    {"dt": "Role", "filters": [["role_name", "in", ["FlowDrive Admin", "FlowDrive User"]]]}
]

after_install = "telegram_drive.install.after_install"
after_migrate = [
    "telegram_drive.install.ensure_settings",
    "telegram_drive.install.ensure_workspace",
    "telegram_drive.install.ensure_activity_log_permission",
    "telegram_drive.install.ensure_activity_log_status_options",
]

add_to_apps_screen = [
    {
        "name": "telegram_drive",
        "logo": "/assets/telegram_drive/images/flow-drive-logo.png",
        "title": "FlowDrive",
        "route": "/telegram-drive",
        "has_permission": "telegram_drive.permissions.has_app_permission",
    }
]
