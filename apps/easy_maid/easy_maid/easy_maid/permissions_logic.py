from __future__ import annotations

OWNER_ROLES = {"System Manager", "Owner", "Easy Maid Owner"}


def can_transition_visit_status(*, old_status: str | None, new_status: str, roles: set[str], is_assigned_cleaner: bool) -> bool:
    """Return whether a user can move a visit into active/completed states.

    Owners/admins can always transition.
    Non-owners may only transition to In Progress/Completed when assigned.
    Other status changes are handled by normal doc permissions.
    """
    if old_status == new_status:
        return True

    if OWNER_ROLES & roles:
        return True

    if new_status in {"In Progress", "Completed"}:
        return is_assigned_cleaner

    return True
