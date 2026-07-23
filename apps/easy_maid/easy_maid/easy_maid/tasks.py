from __future__ import annotations

from datetime import date, datetime, timedelta

import frappe
from frappe.utils import get_datetime, getdate

from easy_maid.easy_maid.recurrence import RecurrenceRule, generate_dates


def _visit_exists(booking: str, scheduled_start: datetime) -> bool:
    return bool(
        frappe.db.exists(
            "Service Visit",
            {
                "booking": booking,
                "scheduled_start": scheduled_start,
                "docstatus": ["<", 2],
            },
        )
    )


def _build_visit(booking_doc, visit_date: date):
    start_ts = get_datetime(f"{visit_date} 09:00:00")
    end_ts = start_ts + timedelta(hours=2)

    if _visit_exists(booking_doc.name, start_ts):
        return None

    return frappe.get_doc(
        {
            "doctype": "Service Visit",
            "booking": booking_doc.name,
            "customer": booking_doc.customer,
            "service_address": booking_doc.service_address,
            "scheduled_start": start_ts,
            "scheduled_end": end_ts,
            "status": "Scheduled",
        }
    )


def generate_recurring_visits() -> None:
    """Materialize recurring visits idempotently up to a configurable horizon.

    Horizon defaults to 35 days and can be overridden via site config key
    `easymaid_visit_horizon_days`.
    """
    horizon_days = int(frappe.conf.get("easymaid_visit_horizon_days", 35))
    horizon_end = getdate() + timedelta(days=horizon_days)

    booking_names = frappe.get_all(
        "Booking",
        filters={"booking_type": "Recurring", "status": "Active"},
        pluck="name",
    )

    for booking_name in booking_names:
        booking = frappe.get_doc("Booking", booking_name)
        rule = RecurrenceRule(
            frequency=booking.frequency,
            interval=booking.interval or 1,
            start_date=getdate(booking.start_date),
            end_date=getdate(booking.end_date) if booking.end_date else None,
            occurrences=booking.occurrences,
        )

        for scheduled_date in generate_dates(rule, horizon_end):
            visit = _build_visit(booking, scheduled_date)
            if visit:
                visit.insert(ignore_permissions=True)

    frappe.db.commit()
