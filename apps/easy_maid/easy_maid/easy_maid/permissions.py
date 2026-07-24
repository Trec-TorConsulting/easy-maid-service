from __future__ import annotations

import frappe


OWNER_ROLES = {"System Manager", "Owner", "Easy Maid Owner"}
CLEANER_ROLES = {"Employee", "Cleaner", "Easy Maid Cleaner"}
CLIENT_ROLES = {"Customer", "Client", "Easy Maid Client"}


def _roles(user: str | None = None) -> set[str]:
    return set(frappe.get_roles(user or frappe.session.user))


def _employee_for_user(user: str | None = None) -> str | None:
    target = user or frappe.session.user
    return frappe.db.get_value("Employee", {"user_id": target}, "name")


def booking_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return "1=1"

    if CLIENT_ROLES & roles:
        customer = frappe.db.get_value("Customer", {"email_id": user}, "name")
        if not customer:
            return "1=0"
        return f"`tabBooking`.`customer` = {frappe.db.escape(customer)}"

    if CLEANER_ROLES & roles:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            return "1=0"
        return (
            "`tabBooking`.`name` in ("
            "select distinct sv.booking from `tabService Visit` sv "
            "inner join `tabCrew Assignment` ca on ca.parent = sv.name "
            f"where ca.employee = {frappe.db.escape(employee)}"
            ")"
        )

    return "1=0"


def service_visit_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return "1=1"

    if CLIENT_ROLES & roles:
        customer = frappe.db.get_value("Customer", {"email_id": user}, "name")
        if not customer:
            return "1=0"
        return f"`tabService Visit`.`customer` = {frappe.db.escape(customer)}"

    if CLEANER_ROLES & roles:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            return "1=0"
        return (
            "`tabService Visit`.`name` in ("
            "select ca.parent from `tabCrew Assignment` ca "
            f"where ca.employee = {frappe.db.escape(employee)}"
            ")"
        )

    return "1=0"


def service_visit_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return True

    if CLIENT_ROLES & roles:
        customer = frappe.db.get_value("Customer", {"email_id": user}, "name")
        return bool(customer and doc.customer == customer)

    if CLEANER_ROLES & roles:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            return False
        return bool(
            frappe.db.exists(
                "Crew Assignment",
                {
                    "parent": doc.name,
                    "parenttype": "Service Visit",
                    "employee": employee,
                },
            )
        )

    return False


def employee_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return "1=1"

    if CLEANER_ROLES & roles:
        employee = _employee_for_user(user)
        if not employee:
            return "1=0"
        return f"`tabEmployee`.`name` = {frappe.db.escape(employee)}"

    return "1=0"


def employee_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return True

    if CLEANER_ROLES & roles:
        employee = _employee_for_user(user)
        return bool(employee and doc.name == employee)

    return False


def salary_slip_query(user=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return "1=1"

    if CLEANER_ROLES & roles:
        employee = _employee_for_user(user)
        if not employee:
            return "1=0"
        return f"`tabSalary Slip`.`employee` = {frappe.db.escape(employee)}"

    return "1=0"


def salary_slip_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    roles = _roles(user)

    if OWNER_ROLES & roles:
        return True

    if CLEANER_ROLES & roles:
        employee = _employee_for_user(user)
        return bool(employee and doc.employee == employee)

    return False
