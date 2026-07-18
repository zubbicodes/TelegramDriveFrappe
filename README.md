<p align="center">
  <img src="telegram_drive/telegram_drive/public/images/telegram-drive.svg" alt="Telegram Drive" width="96" height="96">
</p>

<h1 align="center">Telegram Drive for Frappe</h1>

<p align="center">
  A mountable Frappe app that turns Telegram Saved Messages into private cloud storage for ERPNext, HRMS, Raven, and other Frappe sites.
</p>

<p align="center">
  <strong>Frappe-native access control</strong> · <strong>Telegram-backed storage</strong> · <strong>Activity Log audit trail</strong>
</p>

## Overview

Telegram Drive is a self-hosted Frappe app for storing files in Telegram while managing file metadata, access, audit logs, and user permissions inside Frappe.

The app is designed to be mounted into an existing Docker-based Frappe instance. Users access it from the Frappe Desk app launcher or directly at `/telegram-drive`.

## Features

- Telegram Saved Messages backed file storage
- Frappe Desk app entry and workspace
- Frappe user session based access
- Role based access with `Telegram Drive Admin` and `Telegram Drive User`
- Per-user permissions for upload, download, delete, folder management, sharing, and moving files
- Upload and download progress tracking
- Chunked upload support for larger files
- Folder management
- File preview for supported text/PDF formats
- Temporary download staging with cleanup
- Cloud notes
- Public share links
- Frappe Activity Log entries for upload, download, and delete actions
- Frappe Desk theme support, including light, dark, and automatic themes
- Docker Compose mount workflow for existing self-hosted Frappe stacks

## Roles And Permissions

Telegram Drive installs two roles:

- `Telegram Drive Admin`: full drive access, permission management, settings, and audit log visibility
- `Telegram Drive User`: can access the drive, with actions controlled by user-specific permissions

Per-user access is managed through `Telegram Drive User Permission`:

- Upload access
- Download access
- Delete file access
- Create/delete folder access
- Share link access
- Move file access

## Activity Logs

Telegram Drive writes audit records to Frappe `Activity Log`.

Search Activity Log for:

```text
Telegram Drive
```

Logged actions include:

- `Telegram Drive Upload: filename`
- `Telegram Drive Download: filename`
- `Telegram Drive Delete: filename`

The Activity Log status column shows:

- `Upload`
- `Download`
- `Delete`

## Telegram Authorization

The drive owner signs in with Telegram API credentials:

- API ID
- API Hash
- Telegram phone number
- optional proxy configuration

After owner authorization, permitted Frappe users can use the same Telegram-backed drive through their own Frappe sessions.

## Docker Mounting

For mounting this app into an already running Docker Compose based Frappe instance, see:

[MOUNTING_GUIDE.md](MOUNTING_GUIDE.md)

The guide contains only the `.env` and compose snippets needed to pull this repository from GitHub and mount it into an existing Frappe service.

## App Structure

```text
telegram_drive/
  frontend/                     React frontend for /telegram-drive
  telegram_drive/
    api/                        Frappe whitelisted API methods
    services/                   Telegram, permissions, activity, temp file services
    telegram_drive/doctype/     Frappe DocTypes
    public/                     Built assets and app logo
    www/telegram-drive/         Frappe web route
```

## Installed Frappe Records

The app install/migrate hooks create or repair:

- Telegram Drive roles
- Telegram Drive workspace/app launcher entry
- Telegram Drive DocTypes
- default drive settings
- private temp/session folders
- Activity Log read/export permission for Telegram Drive admins
- Activity Log statuses for upload, download, and delete

## Requirements

- Frappe `>=14`
- Python `>=3.10`
- Docker-based Frappe bench recommended
- Telegram API credentials from Telegram

Python dependencies:

- `telethon`
- `PySocks`
- `aiofiles`

## License

MIT
