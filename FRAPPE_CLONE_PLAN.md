# Telegram Drive to Frappe/ERPNext Clone Plan

## Objective

Clone this Telegram Drive project as a custom Frappe app installed on an existing ERPNext site, while preserving the current application behavior and structure as closely as possible.

The cloned app should continue using Telegram Saved Messages as the real storage backend. Frappe/ERPNext should replace the current FastAPI and SQLite metadata layer, while the existing React interface can be reused with API changes.

## Current Project Summary

This project is a personal cloud drive powered by Telegram Saved Messages.

Current stack:

- Backend: FastAPI, Python, Telethon, SQLite
- Frontend: React, Vite, Tailwind CSS, Axios, Lucide React
- Storage backend: Telegram Saved Messages
- Local storage: SQLite metadata, Telegram session files, temp upload/download files

Current project structure:

```text
backend/
  main.py
  telegram_service.py
  database.py
  requirements.txt

frontend/
  src/
    App.jsx
    api.js
    components/
      AuthScreen.jsx
      FileManager.jsx
      PortalManager.jsx
      CloudNotes.jsx
```

The current app stores actual file bytes in the owner's Telegram Saved Messages. The local database stores only metadata such as folder hierarchy, file names, file sizes, Telegram message IDs, portal users, share links, settings, and cloud notes.

## Core Features To Preserve

- Owner Telegram login using phone number, API ID, API hash, verification code, and optional 2FA password.
- Optional proxy support:
  - SOCKS5
  - MTProto
- Upload files from browser to server.
- Upload files from server to Telegram Saved Messages.
- Store metadata locally in the app database.
- Folder creation and nested folder browsing.
- File browsing in grid/list style.
- Breadcrumb navigation.
- File search.
- File upload progress.
- Chunked uploads for large files.
- File download from Telegram through server temp storage.
- Download progress.
- File preview for supported text/PDF types.
- File move between folders.
- File deletion from metadata and Telegram.
- Public share links.
- Friend portal users.
- Friend download-only access.
- Friend upload permission when allowed.
- Shared CloudNote notes.
- Drive name setting.
- Temp file listing and cleanup.
- Light/dark theme behavior in frontend.

## Target Frappe App

Suggested app name:

```text
telegram_drive
```

Create and install:

```bash
cd frappe-bench
bench new-app telegram_drive
bench --site your-site-name install-app telegram_drive
```

Suggested Frappe app structure:

```text
telegram_drive/
  telegram_drive/
    api/
      auth.py
      files.py
      folders.py
      portal.py
      notes.py
      settings.py
      transfers.py
    services/
      telegram_service.py
      progress.py
      temp_files.py
      security.py
    scripts/
      import_sqlite.py
    www/
      telegram-drive/
        index.html
    public/
      js/
      css/
    hooks.py
    patches.txt
  frontend/
    src/
```

## Python Dependencies

Add these dependencies to the custom app:

```text
telethon
PySocks
aiofiles
```

Install them in the bench environment:

```bash
bench pip install telethon PySocks aiofiles
bench restart
```

## Storage Design

Telegram must remain the real storage backend.

Frappe/MariaDB will store:

- Owner connection metadata
- Folder records
- File records
- Telegram message IDs
- Portal users
- Portal sessions
- Public share tokens
- Settings
- Cloud notes
- Transfer progress metadata if needed

Frappe should not store uploaded files permanently in its normal `File` DocType unless a temporary pointer is required. The actual file content should continue to live in Telegram Saved Messages.

Private local paths should be inside the ERPNext site directory:

```python
frappe.get_site_path("private", "telegram_drive", "sessions")
frappe.get_site_path("private", "telegram_drive", "temp")
```

The Telegram session directory is sensitive and must not be publicly accessible.

## DocTypes

### 1. Telegram Drive Owner

Purpose: stores Telegram owner account and connection settings.

Fields:

- `phone` - Data, unique
- `api_id` - Int
- `api_hash` - Password
- `session_name` - Data
- `phone_code_hash` - Data
- `is_authorized` - Check
- `proxy_type` - Select: `none`, `socks5`, `mtproto`
- `proxy_host` - Data
- `proxy_port` - Int
- `proxy_secret` - Password
- `proxy_username` - Data
- `proxy_password` - Password

Notes:

- Only one active authorized owner is required to match the current app.
- Multiple owners can be supported later, but the first version should keep the current single-owner model.

### 2. Telegram Drive Folder

Purpose: replaces the current SQLite `folders` table.

Fields:

- `folder_name` - Data
- `parent_folder` - Link to `Telegram Drive Folder`
- `created_at` - Datetime
- `created_by_label` - Data, optional

Notes:

- A normal self-linked DocType is enough.
- Frappe tree behavior can be added later if desired.

### 3. Telegram Drive File

Purpose: replaces the current SQLite `files` table.

Fields:

- `telegram_message_id` - Int
- `file_name` - Data
- `file_size` - Int
- `mime_type` - Data
- `folder` - Link to `Telegram Drive Folder`
- `uploaded_by_label` - Data
- `created_at` - Datetime

Notes:

- This DocType stores metadata only.
- `telegram_message_id` is the critical field that maps a file record to Telegram Saved Messages.

### 4. Telegram Drive Portal User

Purpose: replaces the current SQLite `portal_users` table.

Fields:

- `username` - Data, unique
- `password_hash` - Password or Data
- `can_upload` - Check
- `enabled` - Check
- `created_at` - Datetime
- `last_login` - Datetime

Notes:

- This keeps friend accounts separate from ERPNext users, matching the current app.
- A future version could map friend users to native Frappe `User` records, but that is not required for an exact clone.

### 5. Telegram Drive Portal Session

Purpose: replaces the current SQLite `portal_sessions` table.

Fields:

- `token` - Data, unique
- `portal_user` - Link to `Telegram Drive Portal User`
- `created_at` - Datetime
- `expires_at` - Datetime, optional

### 6. Telegram Drive Share

Purpose: replaces the current SQLite `file_shares` table.

Fields:

- `token` - Data, unique
- `drive_file` - Link to `Telegram Drive File`
- `enabled` - Check
- `created_at` - Datetime
- `expires_at` - Datetime, optional
- `download_count` - Int, optional

### 7. Telegram Drive Setting

Purpose: replaces current app settings.

Recommended as a Single DocType.

Fields:

- `drive_name` - Data, default `My Drive`
- `temp_retention_hours` - Int, default `6`
- `chunk_size_mb` - Int, default `25`
- `large_upload_threshold_mb` - Int, default `50`

### 8. Telegram Drive Cloud Note

Purpose: replaces the current SQLite `cloud_notes` table.

Fields:

- `title` - Data
- `body` - Text
- `color` - Select: `yellow`, `blue`, `green`, `pink`, `violet`
- `created_by_label` - Data
- `created_at` - Datetime
- `updated_at` - Datetime

## Roles And Permissions

Create Frappe roles:

- `Telegram Drive Admin`
- `Telegram Drive User`, optional

Admin permissions:

- Connect Telegram owner account
- Manage drive settings
- Create folders
- Upload files
- Download files
- Move files
- Delete files
- Create share links
- Manage friend portal accounts
- Manage cloud notes
- View and delete temp files

Portal user permissions:

- Browse folders and files
- Download files
- Create public share links if allowed
- Create/edit/delete cloud notes
- Upload files and create folders only when `can_upload` is enabled

Public permissions:

- Download a file only when a valid share token exists.

## Telegram Service Port

Move the existing logic from:

```text
backend/telegram_service.py
```

to:

```text
telegram_drive/telegram_drive/services/telegram_service.py
```

Preserve behavior:

- Telethon client cache
- Telegram session files
- `send_code`
- `sign_in_code`
- `sign_in_password`
- `upload_file`
- `download_file`
- `get_message`
- `delete_message`
- SOCKS5 proxy support
- MTProto proxy support

Change session path handling:

```python
SESSIONS_DIR = frappe.get_site_path("private", "telegram_drive", "sessions")
```

Change temp path handling:

```python
TEMP_DIR = frappe.get_site_path("private", "telegram_drive", "temp")
```

## Frappe API Mapping

Replace FastAPI routes with Frappe whitelisted methods.

### Owner Auth

Current routes:

```text
POST /api/auth/start
POST /api/auth/code
POST /api/auth/password
GET  /api/auth/me
```

Frappe methods:

```text
/api/method/telegram_drive.api.auth.start
/api/method/telegram_drive.api.auth.verify_code
/api/method/telegram_drive.api.auth.verify_password
/api/method/telegram_drive.api.auth.me
```

### Settings

Current routes:

```text
GET /api/settings
PUT /api/settings
GET /api/storage/summary
```

Frappe methods:

```text
/api/method/telegram_drive.api.settings.get_settings
/api/method/telegram_drive.api.settings.update_settings
/api/method/telegram_drive.api.settings.storage_summary
```

### Folders

Current routes:

```text
GET    /api/folders
GET    /api/folders/all
POST   /api/folders
DELETE /api/folders/{folder_id}
```

Frappe methods:

```text
/api/method/telegram_drive.api.folders.list
/api/method/telegram_drive.api.folders.list_all
/api/method/telegram_drive.api.folders.create
/api/method/telegram_drive.api.folders.delete
```

### Files

Current routes:

```text
GET    /api/files
POST   /api/files/upload
POST   /api/files/upload-chunk
GET    /api/upload-progress/{upload_id}
POST   /api/files/{file_id}/start-download
GET    /api/download-progress/{download_id}
GET    /api/temp-download/{download_id}
GET    /api/files/{file_id}/download
POST   /api/files/{file_id}/share
DELETE /api/files/{file_id}
PUT    /api/files/{file_id}/move
GET    /api/temp-files
DELETE /api/temp-files/{filename}
```

Frappe methods:

```text
/api/method/telegram_drive.api.files.list
/api/method/telegram_drive.api.files.upload
/api/method/telegram_drive.api.files.upload_chunk
/api/method/telegram_drive.api.transfers.upload_progress
/api/method/telegram_drive.api.files.start_download
/api/method/telegram_drive.api.transfers.download_progress
/api/method/telegram_drive.api.files.temp_download
/api/method/telegram_drive.api.files.download
/api/method/telegram_drive.api.files.create_share_link
/api/method/telegram_drive.api.files.delete
/api/method/telegram_drive.api.files.move
/api/method/telegram_drive.api.transfers.list_temp_files
/api/method/telegram_drive.api.transfers.delete_temp_file
```

### Public Share

Current route:

```text
GET /api/share/{share_token}
```

Frappe method or website route:

```text
/api/method/telegram_drive.api.files.public_share_download
```

or a nicer public route:

```text
/telegram-drive/share/<token>
```

### Portal

Current routes:

```text
POST /api/portal/login
GET  /api/portal/me
POST /api/portal/password
GET  /api/portal/settings
GET  /api/portal/storage/summary
GET  /api/portal/users
POST /api/portal/users
PUT  /api/portal/users/{user_id}
DELETE /api/portal/users/{user_id}
GET  /api/portal/folders
POST /api/portal/folders
GET  /api/portal/files
POST /api/portal/files/upload
POST /api/portal/files/upload-chunk
POST /api/portal/files/{file_id}/share
GET  /api/portal/upload-progress/{upload_id}
POST /api/portal/files/{file_id}/start-download
GET  /api/portal/download-progress/{download_id}
GET  /api/portal/temp-download/{download_id}
GET  /api/portal/files/{file_id}/download
```

Frappe methods:

```text
/api/method/telegram_drive.api.portal.login
/api/method/telegram_drive.api.portal.me
/api/method/telegram_drive.api.portal.change_password
/api/method/telegram_drive.api.portal.get_settings
/api/method/telegram_drive.api.portal.storage_summary
/api/method/telegram_drive.api.portal.list_users
/api/method/telegram_drive.api.portal.create_user
/api/method/telegram_drive.api.portal.update_user
/api/method/telegram_drive.api.portal.delete_user
/api/method/telegram_drive.api.portal.list_folders
/api/method/telegram_drive.api.portal.create_folder
/api/method/telegram_drive.api.portal.list_files
/api/method/telegram_drive.api.portal.upload
/api/method/telegram_drive.api.portal.upload_chunk
/api/method/telegram_drive.api.portal.create_share_link
/api/method/telegram_drive.api.portal.upload_progress
/api/method/telegram_drive.api.portal.start_download
/api/method/telegram_drive.api.portal.download_progress
/api/method/telegram_drive.api.portal.temp_download
/api/method/telegram_drive.api.portal.download
```

### Cloud Notes

Current routes:

```text
GET    /api/cloud-notes
POST   /api/cloud-notes
PUT    /api/cloud-notes/{note_id}
DELETE /api/cloud-notes/{note_id}
GET    /api/portal/cloud-notes
POST   /api/portal/cloud-notes
PUT    /api/portal/cloud-notes/{note_id}
DELETE /api/portal/cloud-notes/{note_id}
```

Frappe methods:

```text
/api/method/telegram_drive.api.notes.list
/api/method/telegram_drive.api.notes.create
/api/method/telegram_drive.api.notes.update
/api/method/telegram_drive.api.notes.delete
/api/method/telegram_drive.api.portal.list_notes
/api/method/telegram_drive.api.portal.create_note
/api/method/telegram_drive.api.portal.update_note
/api/method/telegram_drive.api.portal.delete_note
```

## Upload Flow

Preserve the current upload model.

Current behavior:

1. Browser sends file to backend.
2. Backend writes file to local temp storage.
3. Backend uploads temp file to Telegram Saved Messages.
4. Telegram returns a message ID.
5. Backend creates file metadata record.
6. Backend deletes local temp file.

Frappe behavior should be:

1. Browser sends file or chunk to Frappe endpoint.
2. Frappe writes temp file under `sites/{site}/private/telegram_drive/temp`.
3. For large files, append chunks until complete.
4. Once complete, enqueue Telegram upload with `frappe.enqueue`.
5. Upload to Telegram Saved Messages through Telethon.
6. Create `Telegram Drive File` record with `telegram_message_id`.
7. Remove local temp file.
8. Store progress in Redis cache.

Recommended chunk settings:

- Chunk size: 25 MB
- Large upload threshold: 50 MB

These match the current frontend constants.

## Download Flow

Preserve the current download model.

Current behavior:

1. User requests download.
2. Backend looks up file metadata.
3. Backend fetches the Telegram message by ID.
4. Backend downloads Telegram media to temp file.
5. Browser downloads temp file from backend.
6. Temp file is cleaned up later.

Frappe behavior should be:

1. User starts download.
2. Frappe creates `download_id`.
3. Frappe enqueues Telegram download.
4. Progress is stored in Redis.
5. Browser polls progress.
6. When complete, browser downloads from temp endpoint.
7. Temp file is removed after configured retention period.

## Progress Tracking

The current app uses in-memory dictionaries:

```python
UPLOAD_PROGRESS = {}
DOWNLOAD_PROGRESS = {}
```

In Frappe, use Redis through:

```python
frappe.cache()
```

Suggested cache keys:

```text
telegram_drive:upload:{upload_id}
telegram_drive:download:{download_id}
```

Progress payload should keep the same shape as the current app:

```json
{
  "percent": 0,
  "stage": "Waiting",
  "done": false,
  "error": null,
  "bytes_done": null,
  "bytes_total": null,
  "speed_bps": null
}
```

For downloads also include:

```json
{
  "temp_path": null,
  "filename": null
}
```

## Frontend Migration

Recommended approach: keep the current React frontend and adapt API calls to Frappe.

This gives the closest clone of the app as it is.

Steps:

1. Copy the existing `frontend` directory into the Frappe app.
2. Update `frontend/src/api.js`.
3. Replace FastAPI route URLs with Frappe method URLs.
4. Keep local storage keys:
   - `td_token`
   - `td_portal_token`
   - `td_theme`
5. Build with Vite.
6. Copy or configure the build output into:

```text
telegram_drive/telegram_drive/www/telegram-drive/
```

The app should be accessible at:

```text
https://your-erpnext-site.com/telegram-drive
```

## Authentication Model

### Owner

Use Frappe authentication for owner/admin access.

Recommended:

- ERPNext user logs into ERPNext normally.
- User must have `Telegram Drive Admin` role.
- Admin can connect the Telegram owner account through the Telegram Drive UI.

Telegram owner login still works exactly like the current app:

- Phone number
- API ID
- API hash
- Optional proxy
- Verification code
- Optional Telegram 2FA password

### Friend Portal

Keep a separate friend portal login system, matching the current app.

Friend users:

- Do not need Telegram accounts.
- Do not need ERPNext accounts.
- Log in with username and password.
- Receive a portal token.
- Use the owner's Telegram account for storage operations.

## Security Requirements

- Store Telegram sessions in the site private directory.
- Do not expose session files through public routes.
- Store `api_hash` and proxy secrets in Password fields.
- Do not log Telegram passwords or proxy passwords.
- Public share links should use long random tokens.
- Friend passwords must be hashed, not stored as plain text.
- Portal tokens should be random UUID or stronger.
- Consider token expiry for portal sessions and public shares.
- Only `Telegram Drive Admin` should manage Telegram credentials.

## SQLite Migration Plan

If existing data must be preserved, migrate the SQLite database into Frappe DocTypes.

Backup first:

```text
backend/telegram_drive.db
backend/sessions/
```

Create script:

```text
telegram_drive/telegram_drive/scripts/import_sqlite.py
```

Migration mapping:

| SQLite Table | Frappe DocType |
|---|---|
| `users` | `Telegram Drive Owner` |
| `folders` | `Telegram Drive Folder` |
| `files` | `Telegram Drive File` |
| `portal_users` | `Telegram Drive Portal User` |
| `portal_sessions` | `Telegram Drive Portal Session` |
| `file_shares` | `Telegram Drive Share` |
| `app_settings` | `Telegram Drive Setting` |
| `cloud_notes` | `Telegram Drive Cloud Note` |

Important:

- Do not re-upload files to Telegram during migration.
- Preserve every `telegram_message_id`.
- Copy existing Telethon session files into:

```text
sites/your-site/private/telegram_drive/sessions/
```

After migration, test downloading several old files. If the Telegram message IDs resolve, migration is successful.

## Implementation Phases

### Phase 1: Frappe Foundation

- Create custom app.
- Install app on ERPNext site.
- Add dependencies.
- Create roles.
- Create DocTypes.
- Create private session and temp directories.
- Create settings Single DocType.

### Phase 2: Telegram Service

- Port Telethon service from the current backend.
- Update session path handling.
- Update proxy handling.
- Implement owner auth start/code/password flow.
- Validate Telegram login with and without proxy.

### Phase 3: Metadata APIs

- Implement folder APIs.
- Implement file list/move/delete APIs.
- Implement settings APIs.
- Implement storage summary calculation.
- Match current response shapes where possible to reduce frontend changes.

### Phase 4: Upload Pipeline

- Implement direct upload endpoint.
- Implement chunk upload endpoint.
- Store chunks in private temp directory.
- Enqueue final Telegram upload.
- Save file record after Telegram upload.
- Store upload progress in Redis.
- Delete upload temp files after completion or failure.

### Phase 5: Download Pipeline

- Implement start-download endpoint.
- Enqueue Telegram download.
- Store download progress in Redis.
- Serve completed temp download file.
- Clean up old temp downloads.
- Add temp file listing and delete APIs for admins.

### Phase 6: Portal System

- Implement portal user CRUD.
- Implement portal login.
- Implement portal token validation.
- Implement portal password change.
- Implement portal folder/file browsing.
- Implement portal upload only when `can_upload` is enabled.
- Implement portal download.
- Implement portal share link creation.

### Phase 7: Public Sharing

- Implement share token creation.
- Implement public share download.
- Add optional expiry and disable support.
- Add optional download count tracking.

### Phase 8: Cloud Notes

- Implement owner notes APIs.
- Implement portal notes APIs.
- Preserve validation:
  - Title max 80 characters
  - Body max 4000 characters
  - Allowed colors: yellow, blue, green, pink, violet

### Phase 9: React Frontend Integration

- Copy current React frontend.
- Update API client for Frappe endpoints.
- Preserve owner/friend mode switching.
- Preserve theme behavior.
- Preserve upload/download progress UI.
- Preserve file preview behavior.
- Build and serve inside Frappe at `/telegram-drive`.

### Phase 10: Migration

- Stop current app.
- Backup SQLite and sessions.
- Run import script.
- Copy Telethon sessions.
- Compare record counts.
- Test old file downloads.
- Test old share links if preserving tokens.

### Phase 11: Testing And Hardening

- Test owner login without proxy.
- Test owner login with SOCKS5 proxy.
- Test owner login with MTProto proxy.
- Test small upload.
- Test large chunked upload.
- Test owner download.
- Test portal download-only user.
- Test portal upload-enabled user.
- Test public share link.
- Test file delete from Telegram.
- Test folder delete.
- Test file move.
- Test notes CRUD.
- Test temp cleanup.
- Test ERPNext permissions.
- Test after bench restart.

## Key Risks

- Frappe request size limits may block large direct uploads. Chunked uploads should be implemented early.
- Telethon is async while many Frappe flows are synchronous. Use queued jobs and careful async wrappers.
- In-memory progress dictionaries will not work reliably across Frappe workers. Use Redis cache.
- Telegram session files are sensitive. They must stay in the private site path.
- Public share download can be slow because Frappe must download from Telegram before serving the file.
- Telegram API limits still apply.
- Deleting a file should attempt Telegram deletion first, but metadata cleanup should handle Telegram failures gracefully.
- Folder deletion must recursively handle child folders and files more safely than the current simple SQLite delete.

## Recommended Final Architecture

Use Frappe/ERPNext as the application and metadata platform, but keep Telegram Saved Messages as the actual storage provider.

Recommended final shape:

- Frappe custom app: `telegram_drive`
- MariaDB DocTypes replace SQLite tables
- Telethon service reused from current app
- Telegram sessions stored in site private directory
- Temp uploads/downloads stored in site private directory
- Redis cache stores progress state
- Frappe background jobs handle Telegram uploads/downloads
- Existing React frontend reused and served at `/telegram-drive`
- ERPNext role controls owner/admin access
- Custom portal user system preserves friend login behavior
- Public share links remain token-based

This approach gives the closest clone of the current app while making it native to the running ERPNext/Frappe environment.
