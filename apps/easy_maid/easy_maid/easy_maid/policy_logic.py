from __future__ import annotations

from datetime import timedelta


POLICY_HOURS = 24


def can_client_modify_visit(scheduled_start, now) -> bool:
    return scheduled_start - now >= timedelta(hours=POLICY_HOURS)
