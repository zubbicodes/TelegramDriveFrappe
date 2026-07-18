# Telegram Drive Mount Snippets

Use these snippets as an override/addition to an already working Frappe Docker Compose stack.

Replace the GitHub URL with the repo you push this project to.

## `.env` Additions

```env
TELEGRAM_DRIVE_GIT_URL=https://github.com/YOUR_USER/YOUR_REPO.git
TELEGRAM_DRIVE_GIT_BRANCH=main
```

Your existing `.env` should already provide the Frappe site variable used by your stack, for example:

```env
SITE_NAME=your-site.localhost
```

## Compose Additions

Add the volume and clone service below, then merge the `frappe` additions into your existing `frappe` service.

```yaml
volumes:
  telegram-drive-source:

services:
  telegram-drive-source:
    image: alpine/git:latest
    restart: "no"
    environment:
      TELEGRAM_DRIVE_GIT_URL: ${TELEGRAM_DRIVE_GIT_URL}
      TELEGRAM_DRIVE_GIT_BRANCH: ${TELEGRAM_DRIVE_GIT_BRANCH:-main}
    volumes:
      - telegram-drive-source:/src
    command:
      - sh
      - -lc
      - |
        set -e
        if [ -d /src/.git ]; then
          git -C /src fetch origin "${TELEGRAM_DRIVE_GIT_BRANCH}"
          git -C /src checkout "${TELEGRAM_DRIVE_GIT_BRANCH}"
          git -C /src reset --hard "origin/${TELEGRAM_DRIVE_GIT_BRANCH}"
        else
          rm -rf /src/*
          git clone --branch "${TELEGRAM_DRIVE_GIT_BRANCH}" "${TELEGRAM_DRIVE_GIT_URL}" /src
        fi

  frappe:
    depends_on:
      telegram-drive-source:
        condition: service_completed_successfully
    volumes:
      - telegram-drive-source:/workspace/TelegramDriveFrappe:rw
    command:
      - bash
      - -lc
      - |
        set -e

        ln -sf /home/frappe/.local/bin/bench /usr/local/bin/bench

        NODE_BIN="$(find /home/frappe/.nvm/versions/node -maxdepth 2 -type f -name yarn -printf "%h\n" 2>/dev/null | sort -V | tail -n 1)"
        if [ -n "${NODE_BIN}" ]; then
          ln -sf "${NODE_BIN}/node" /usr/local/bin/node
          ln -sf "${NODE_BIN}/npm" /usr/local/bin/npm
          ln -sf "${NODE_BIN}/yarn" /usr/local/bin/yarn
        fi

        exec su frappe -s /bin/bash -c '
        set -e

        export HOME="/home/frappe"
        export NVM_DIR="${NVM_DIR:-/home/frappe/.nvm}"
        if [ -s "${NVM_DIR}/nvm.sh" ]; then
          . "${NVM_DIR}/nvm.sh"
        fi

        NODE_BIN="$(find "${NVM_DIR}/versions/node" -maxdepth 2 -type f -name yarn -printf "%h\n" 2>/dev/null | sort -V | tail -n 1)"
        export PATH="/usr/local/bin:/home/frappe/.local/bin:/home/frappe/.pyenv/shims:/home/frappe/.pyenv/bin:${NODE_BIN}:${PATH}"

        SITE_NAME="${SITE_NAME:?SITE_NAME is required}"
        BENCH_DIR="/home/frappe/frappe-bench"
        REPO_MOUNT="/workspace/TelegramDriveFrappe"
        APP_MOUNT="${REPO_MOUNT}/telegram_drive"
        APP_NAME="telegram_drive"

        cd "${BENCH_DIR}"

        rm -rf "apps/${APP_NAME}"
        ln -s "${APP_MOUNT}" "apps/${APP_NAME}"

        "${BENCH_DIR}/env/bin/python" -m pip install --quiet telethon PySocks aiofiles
        "${BENCH_DIR}/env/bin/python" -m pip install --quiet -e "apps/${APP_NAME}"

        if ! grep -qx "${APP_NAME}" sites/apps.txt; then
          printf "\n%s\n" "${APP_NAME}" >> sites/apps.txt
        fi

        bench use "${SITE_NAME}"

        if ! bench --site "${SITE_NAME}" list-apps | awk "{print \$1}" | grep -qx "${APP_NAME}"; then
          bench --site "${SITE_NAME}" install-app "${APP_NAME}"
        else
          bench --site "${SITE_NAME}" migrate
        fi

        bench build --app "${APP_NAME}" || true
        bench --site "${SITE_NAME}" set-config ignore_csrf 1
        bench --site "${SITE_NAME}" clear-cache
        bench --site "${SITE_NAME}" clear-website-cache

        bench start
        '
```

This snippet assumes your existing `frappe` service already has its normal image, networks, ports, database variables, Redis variables, and `frappe-bench` volume.
