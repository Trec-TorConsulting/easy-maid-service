from __future__ import annotations

import frappe

from easy_maid.easy_maid.booking_policy import enforce_24h_notice


@frappe.whitelist()
def dispatch_board(start_date: str, end_date: str | None = None):
    """Return visits grouped for owner dispatch UI."""
    end_date = end_date or start_date

    visits = frappe.get_all(
        "Service Visit",
        filters={"scheduled_start": ["between", [start_date, end_date]]},
        fields=[
            "name",
            "booking",
            "customer",
            "service_address",
            "scheduled_start",
            "scheduled_end",
            "status",
        ],
        order_by="scheduled_start asc",
    )

    for visit in visits:
        visit["crew"] = frappe.get_all(
            "Crew Assignment",
            filters={"parent": visit["name"], "parenttype": "Service Visit"},
            fields=["employee", "role"],
            order_by="idx asc",
        )
        visit["unassigned"] = len(visit["crew"]) == 0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "visits": visits,
    }


@frappe.whitelist()
def crew_calendar(employee: str | None = None, status: str | None = None):
    filters = {}
    if status:
        filters["status"] = status

    fields = [
        "name",
        "booking",
        "customer",
        "service_address",
        "scheduled_start",
        "scheduled_end",
        "status",
    ]

    visits = frappe.get_all("Service Visit", filters=filters, fields=fields, order_by="scheduled_start asc")

    if employee:
        allowed = {
            row.parent
            for row in frappe.get_all(
                "Crew Assignment",
                filters={"parenttype": "Service Visit", "employee": employee},
                fields=["parent"],
            )
        }
        visits = [v for v in visits if v["name"] in allowed]

    return visits


@frappe.whitelist()
def mark_visit_status(visit_name: str, status: str, notes: str | None = None):
    visit = frappe.get_doc("Service Visit", visit_name)
    visit.status = status
    if notes:
        visit.notes = notes
    visit.save()
    return {"name": visit.name, "status": visit.status}


@frappe.whitelist()
def cancel_service_visit(visit_name: str, reason: str | None = None):
    visit = frappe.get_doc("Service Visit", visit_name)
    enforce_24h_notice(visit)
    visit.status = "Cancelled"
    if reason:
        visit.notes = (visit.notes or "") + f"\nCancel reason: {reason}"
    visit.save()
    return {"name": visit.name, "status": visit.status}


@frappe.whitelist()
def reschedule_service_visit(visit_name: str, scheduled_start: str, scheduled_end: str):
    visit = frappe.get_doc("Service Visit", visit_name)
    enforce_24h_notice(visit)
    visit.scheduled_start = scheduled_start
    visit.scheduled_end = scheduled_end
    visit.status = "Scheduled"
    visit.save()
    return {
        "name": visit.name,
        "status": visit.status,
        "scheduled_start": visit.scheduled_start,
        "scheduled_end": visit.scheduled_end,
    }


@frappe.whitelist()
def create_booking_from_sales_order(sales_order: str, booking_type: str = "One-time"):
    so = frappe.get_doc("Sales Order", sales_order)
    booking = frappe.new_doc("Booking")
    booking.customer = so.customer
    booking.booking_type = booking_type
    booking.status = "Active"
    booking.sales_order = so.name

    if so.items:
        for item in so.items:
            booking.append(
                "services",
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                },
            )

    booking.insert(ignore_permissions=True)
    return booking.name
