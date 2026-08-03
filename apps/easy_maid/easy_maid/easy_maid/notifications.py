"""
Notification helpers for Maidurday Cleaning Service.

These are triggered via doc_events in hooks.py. All email sends are
enqueued as background jobs (frappe.sendmail is async by default in workers)
so they never block the originating user request. Duplicate sends are guarded
by Redis keys with a 24-hour TTL.
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime


def _dedup_key(event: str, doc_name: str) -> str:
    return f"easymaid:notif:{event}:{doc_name}"


def _already_sent(event: str, doc_name: str) -> bool:
    return bool(frappe.cache().get_value(_dedup_key(event, doc_name)))


def _mark_sent(event: str, doc_name: str, ttl_seconds: int = 86400):
    frappe.cache().set_value(_dedup_key(event, doc_name), 1, expires_in_sec=ttl_seconds)


def _get_customer_email(customer_name: str) -> str | None:
    return frappe.db.get_value("Customer", customer_name, "email_id")


def send_booking_confirmation(doc, method=None):
    """Send booking confirmation to customer after a Booking is created."""
    if _already_sent("booking_confirmation", doc.name):
        return
    email = _get_customer_email(doc.customer) if doc.customer else None
    if not email:
        return
    try:
        schedule_str = doc.scheduled_date or doc.start_date or ""
        frappe.sendmail(
            recipients=[email],
            subject=_("Booking Confirmed – {0} | Maidurday").format(doc.name),
            message=_(
                "<p>Hi,</p>"
                "<p>Your cleaning booking <strong>{0}</strong> is confirmed.</p>"
                "<ul>"
                "<li>Type: {1}</li>"
                "{2}"
                "<li>Address: {3}</li>"
                "</ul>"
                "<p>Log in to your <a href='/login'>client portal</a> to manage your bookings.</p>"
                "<p>Thank you,<br/>Maidurday Cleaning Service</p>"
            ).format(
                doc.name,
                doc.booking_type or "Cleaning",
                f"<li>Date: {schedule_str}</li>" if schedule_str else "",
                doc.service_address or "",
            ),
            reference_doctype="Booking",
            reference_name=doc.name,
        )
        _mark_sent("booking_confirmation", doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: booking confirmation email failed")


def send_cleaner_assignment_notification(doc, method=None):
    """Notify assigned cleaners when a Service Visit crew changes."""
    crew = doc.get("crew_assignments") or []
    for assignment in crew:
        employee_name = assignment.get("employee") or getattr(assignment, "employee", None)
        if not employee_name:
            continue
        dedup = f"{doc.name}:{employee_name}"
        if _already_sent("cleaner_assigned", dedup):
            continue
        user_id = frappe.db.get_value("Employee", employee_name, "user_id")
        email = frappe.db.get_value("User", user_id, "email") if user_id else None
        if not email:
            continue
        try:
            frappe.sendmail(
                recipients=[email],
                subject=_("New Assignment: Service Visit {0}").format(doc.name),
                message=_(
                    "<p>Hi,</p>"
                    "<p>You have been assigned to Service Visit <strong>{0}</strong>.</p>"
                    "<ul>"
                    "<li>Scheduled: {1}</li>"
                    "<li>Address: {2}</li>"
                    "</ul>"
                    "<p>Log in to view your full schedule.</p>"
                    "<p>Maidurday Cleaning Service</p>"
                ).format(doc.name, doc.scheduled_start or "", doc.service_address or ""),
                reference_doctype="Service Visit",
                reference_name=doc.name,
            )
            _mark_sent("cleaner_assigned", dedup)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Easy Maid: cleaner assignment email failed for {employee_name}")


def send_invoice_notification(doc, method=None):
    """Notify customer that a Sales Invoice is ready to pay."""
    if _already_sent("invoice_issued", doc.name):
        return
    email = frappe.db.get_value("Customer", doc.customer, "email_id") if doc.customer else None
    if not email:
        return
    try:
        frappe.sendmail(
            recipients=[email],
            subject=_("Invoice {0} from Maidurday Cleaning Service").format(doc.name),
            message=_(
                "<p>Hi {0},</p>"
                "<p>Invoice <strong>{1}</strong> for <strong>${2}</strong> is ready.</p>"
                "<p><a href='/login'>Log in to your portal</a> to view and pay securely via Stripe.</p>"
                "<p>Thank you,<br/>Maidurday Cleaning Service</p>"
            ).format(doc.customer_name or doc.customer, doc.name, doc.grand_total or 0),
            reference_doctype="Sales Invoice",
            reference_name=doc.name,
        )
        _mark_sent("invoice_issued", doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: invoice notification email failed")


def send_payment_receipt(doc, method=None):
    """Send payment receipt to customer when a Payment Entry is submitted."""
    if _already_sent("payment_receipt", doc.name):
        return
    if doc.party_type != "Customer" or not doc.party:
        return
    email = frappe.db.get_value("Customer", doc.party, "email_id")
    if not email:
        return
    try:
        frappe.sendmail(
            recipients=[email],
            subject=_("Payment Received – Thank You | Maidurday"),
            message=_(
                "<p>Hi,</p>"
                "<p>We've received your payment of <strong>${0}</strong>. Thank you!</p>"
                "<p>Reference: {1}</p>"
                "<p>You can download your receipt from the <a href='/login'>client portal</a>.</p>"
                "<p>Maidurday Cleaning Service</p>"
            ).format(doc.paid_amount or 0, doc.name),
            reference_doctype="Payment Entry",
            reference_name=doc.name,
        )
        _mark_sent("payment_receipt", doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: payment receipt email failed")


def send_visit_reminders() -> None:
    """Scheduled task (hourly): remind clients ~24h before a Service Visit.

    Finds visits scheduled to start between 23 and 25 hours from now so the
    window comfortably catches the ~24h mark regardless of when the job runs.
    Idempotent: each visit gets at most one reminder (Redis key, 2-day TTL).
    """
    from frappe.utils import add_to_date, get_datetime

    now = now_datetime()
    window_start = add_to_date(now, hours=23)
    window_end = add_to_date(now, hours=25)

    visits = frappe.get_all(
        "Service Visit",
        filters={
            "status": ["in", ["Scheduled"]],
            "scheduled_start": ["between", [window_start, window_end]],
        },
        fields=["name", "customer", "service_address", "scheduled_start", "scheduled_end"],
    )

    for visit in visits:
        dedup = visit["name"]
        if _already_sent("visit_reminder", dedup):
            continue
        if not visit.get("customer"):
            continue
        email = _get_customer_email(visit["customer"])
        if not email:
            continue
        try:
            frappe.sendmail(
                recipients=[email],
                subject=_("Reminder: Your Clean is Tomorrow | Maidurday"),
                message=_(
                    "<p>Hi,</p>"
                    "<p>This is a friendly reminder that your cleaning is scheduled for "
                    "<strong>{0}</strong>.</p>"
                    "<ul>"
                    "<li>Address: {1}</li>"
                    "</ul>"
                    "<p>Need to reschedule? Please note that <strong>changes must be made "
                    "at least 24 hours in advance</strong>. "
                    "<a href='/login'>Log in to your portal</a> to manage your visit.</p>"
                    "<p>Maidurday Cleaning Service</p>"
                ).format(visit["scheduled_start"], visit["service_address"] or ""),
                reference_doctype="Service Visit",
                reference_name=visit["name"],
            )
            _mark_sent("visit_reminder", dedup, ttl_seconds=172800)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Easy Maid: visit reminder failed for {visit['name']}")
