import json

import frappe


def _key(kind, transfer_id):
    return f"telegram_drive:{kind}:{transfer_id}"


def initial(stage="Waiting"):
    return {
        "percent": 0,
        "stage": stage,
        "done": False,
        "error": None,
        "bytes_done": None,
        "bytes_total": None,
        "speed_bps": None,
    }


def set_progress(kind, transfer_id, payload, expires=86400):
    frappe.cache().set_value(_key(kind, transfer_id), json.dumps(payload), expires_in_sec=expires)
    return payload


def get_progress(kind, transfer_id):
    raw = frappe.cache().get_value(_key(kind, transfer_id))
    if not raw:
        return initial()
    if isinstance(raw, bytes):
        raw = raw.decode()
    return json.loads(raw)


def update_progress(kind, transfer_id, **updates):
    payload = get_progress(kind, transfer_id)
    payload.update(updates)
    return set_progress(kind, transfer_id, payload)
