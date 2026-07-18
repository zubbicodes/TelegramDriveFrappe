import asyncio
import os
import socks

import frappe
from telethon import TelegramClient
from telethon.network.connection.tcpmtproxy import ConnectionTcpMTProxyRandomizedIntermediate

from telegram_drive.services.temp_files import ensure_dirs, sessions_dir

_CLIENTS = {}


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return loop.run_until_complete(coro)


def _secret(doc, fieldname):
    value = doc.get(fieldname)
    if value and value.startswith("*"):
        return doc.get_password(fieldname)
    return value


def _proxy(owner):
    proxy_type = (owner.proxy_type or "none").lower()
    host = owner.proxy_host
    port = owner.proxy_port
    secret = _secret(owner, "proxy_secret")
    username = owner.proxy_username
    password = _secret(owner, "proxy_password")
    if proxy_type == "none" or not any([host, port, secret, username, password]):
        return None
    if proxy_type == "socks5":
        if not all([host, port]):
            raise ValueError("SOCKS5 proxy requires host and port")
        return {"proxy": (socks.SOCKS5, host, int(port), True, username or None, password or None)}
    if proxy_type == "mtproto":
        if not all([host, port, secret]):
            raise ValueError("MTProto proxy requires host, port, and secret")
        return {
            "connection": ConnectionTcpMTProxyRandomizedIntermediate,
            "proxy": (host, int(port), secret),
        }
    raise ValueError("Proxy type must be one of: none, mtproto, socks5")
    return None


def get_owner():
    name = frappe.db.get_value("Telegram Drive Owner", {"is_authorized": 1}, "name")
    if not name:
        name = frappe.db.get_value("Telegram Drive Owner", {}, "name")
    if not name:
        frappe.throw("Telegram owner is not configured")
    return frappe.get_doc("Telegram Drive Owner", name)


def client_for(owner=None):
    ensure_dirs()
    owner = owner or get_owner()
    session_name = owner.session_name or f"telegram_drive_{owner.phone}"
    session_path = os.path.join(sessions_dir(), session_name)
    key = (
        session_name,
        owner.proxy_type or "none",
        owner.proxy_host,
        owner.proxy_port,
        _secret(owner, "proxy_secret"),
        owner.proxy_username,
        bool(_secret(owner, "proxy_password")),
    )
    if key in _CLIENTS:
        client = _CLIENTS[key]
        return client
    proxy = _proxy(owner)
    kwargs = {
        "timeout": 120,
        "connection_retries": 5,
        "request_retries": 5,
        "auto_reconnect": True,
    }
    if proxy:
        kwargs.update(proxy)
    client = TelegramClient(session_path, int(owner.api_id), _secret(owner, "api_hash"), **kwargs)
    _CLIENTS[key] = client
    return client


def send_code(owner):
    async def inner():
        client = client_for(owner)
        await asyncio.wait_for(client.connect(), timeout=30)
        sent = await asyncio.wait_for(client.send_code_request(owner.phone), timeout=30)
        return sent.phone_code_hash
    return _run(inner())


def sign_in_code(owner, code):
    async def inner():
        client = client_for(owner)
        await client.connect()
        await client.sign_in(owner.phone, code, phone_code_hash=owner.phone_code_hash)
        return await client.is_user_authorized()
    return _run(inner())


def sign_in_password(owner, password):
    async def inner():
        client = client_for(owner)
        await client.connect()
        await client.sign_in(password=password)
        return await client.is_user_authorized()
    return _run(inner())


def is_authorized(owner=None):
    async def inner():
        client = client_for(owner)
        await client.connect()
        return await client.is_user_authorized()
    return _run(inner())


def upload_file(path, progress_cb=None):
    async def inner():
        client = client_for()
        await client.connect()
        message = await client.send_file("me", path, progress_callback=progress_cb)
        return message.id
    return _run(inner())


def download_file(message_id, path, progress_cb=None):
    async def inner():
        client = client_for()
        await client.connect()
        message = await client.get_messages("me", ids=int(message_id))
        if not message:
            frappe.throw("Telegram message not found")
        await client.download_media(message, file=path, progress_callback=progress_cb)
        return path
    return _run(inner())


def delete_message(message_id):
    async def inner():
        client = client_for()
        await client.connect()
        await client.delete_messages("me", [int(message_id)])
    return _run(inner())
