from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import get_datetime, now_datetime

from easy_maid.easy_maid.policy_logic import POLICY_HOURS, can_client_modify_visit


def _is_owner_or_admin(user: str) -> bool:
    roles = set(frappe.get_roles(user))
    return bool({"System Manager", "Owner", "Easy Maid Owner"} & roles)


def _is_client_user(user: str) -> bool:
    roles = set(frappe.get_roles(user))
    return bool({"Customer", "Client", "Easy Maid Client"} & roles)


def enforce_24h_notice(doc, method=None):
    """Block client cancel/reschedule changes inside 24h; allow owner override."""
    user = frappe.session.user
    if _is_owner_or_admin(user):
        return

    if not _is_client_user(user):
        return

    start_ts = get_datetime(doc.scheduled_start)
    if not start_ts:
        return

    if not can_client_modify_visit(start_ts, now_datetime()):
        frappe.throw(
            f"At least {POLICY_HOURS} hours notice is required to cancel or reschedule this visit."
        )


def validate_reschedule_window(doc, method=None):
    if doc.is_new():
        return

    old_start = frappe.db.get_value("Service Visit", doc.name, "scheduled_start")
    if not old_start:
        return

    if get_datetime(old_start) != get_datetime(doc.scheduled_start):
        enforce_24h_notice(doc, method)
