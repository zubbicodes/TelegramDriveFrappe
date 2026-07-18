# Telegram Drive

A mountable Frappe/ERPNext app that stores file bytes in Telegram Saved Messages and stores metadata in Frappe DocTypes.

Install inside a bench:

```bash
bench get-app /path/to/telegram_drive
bench --site your-site install-app telegram_drive
bench pip install telethon PySocks aiofiles
bench restart
```

Open `/telegram-drive` on your ERPNext site.
