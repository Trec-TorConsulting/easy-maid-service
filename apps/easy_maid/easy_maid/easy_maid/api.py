from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_days, now_datetime, today

from easy_maid.easy_maid.booking_policy import enforce_24h_notice
from easy_maid.easy_maid.quote_logic import clean_quote_request_payload


def _ensure_owner_or_admin():
    user = frappe.session.user
    roles = set(frappe.get_roles(user))
    allowed = {"System Manager", "Easy Maid Owner"}
    if roles.isdisjoint(allowed):
        frappe.throw(_("Only Owner/Admin can perform this action."))


def _get_mapper(candidates: list[str]):
    for path in candidates:
        try:
            return frappe.get_attr(path)
        except Exception:
            continue
    frappe.throw(_("Required ERPNext mapper not found. Verify ERPNext app installation."))


def _normalize_items(items: str | list[dict] | None) -> list[dict]:
    if not items:
        return []
    if isinstance(items, list):
        return items
    if isinstance(items, str):
        parsed = json.loads(items)
        if isinstance(parsed, list):
            return parsed
    frappe.throw(_("items must be a JSON array"))
    return []


def _current_user_roles() -> set[str]:
    return set(frappe.get_roles(frappe.session.user))


def _current_customer() -> str | None:
    user = frappe.session.user
    return frappe.db.get_value("Customer", {"email_id": user}, "name")


def _current_employee() -> str | None:
    user = frappe.session.user
    return frappe.db.get_value("Employee", {"user_id": user}, "name")


def _ensure_client_or_owner():
    roles = _current_user_roles()
    if roles.isdisjoint({"System Manager", "Easy Maid Owner", "Easy Maid Client", "Customer", "Client"}):
        frappe.throw(_("Only clients or owners can perform this action."))


def _frequency_to_months(frequency: str, interval: int) -> int:
    base = {
        "Weekly": 1,
        "Biweekly": 1,
        "Monthly": 1,
    }.get(frequency, 1)
    return max(base * max(interval, 1), 1)


def _nj_tax_template() -> str | None:
    """Resolve the NJ sales tax template name.

    The template is created with title "NJ Sales Tax"; ERPNext appends the
    company abbreviation to the autoname (e.g. "NJ Sales Tax - EMS"), so the
    link value must be resolved by title rather than hardcoded.
    """
    return frappe.db.get_value(
        "Sales Taxes and Charges Template", {"title": "NJ Sales Tax"}, "name"
    )


def _default_company() -> str | None:
    """Return the global default company, falling back to the only company."""
    return (
        frappe.defaults.get_global_default("company")
        or frappe.db.get_value("Company", {}, "name")
    )


def _resolve_customer_address(so) -> str:
    """Resolve a service address for a Sales Order's customer.

    Prefers the order's own address links, then any Address linked to the
    customer. Raises a clear error when none exists so bookings are never
    created without a serviceable location.
    """
    address = so.customer_address or so.shipping_address_name
    if not address and so.customer:
        address = frappe.db.get_value(
            "Dynamic Link",
            {
                "link_doctype": "Customer",
                "link_name": so.customer,
                "parenttype": "Address",
            },
            "parent",
        )
    if not address:
        frappe.throw(
            _("No service address found for customer {0}. Add an address before creating a booking.").format(
                so.customer
            )
        )
    return address


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
def available_cleaners(scheduled_start: str, scheduled_end: str, service_area: str | None = None):
    """Return cleaners available for a visit window based on shift assignment and visit overlaps."""
    _ensure_owner_or_admin()

    candidates = frappe.get_all(
        "Employee",
        filters={"status": "Active", "designation": ["in", ["Cleaner", "Lead Cleaner"]]},
        fields=["name", "employee_name", "easymaid_service_area", "easymaid_skills", "easymaid_certifications"],
        order_by="employee_name asc",
    )
    if service_area:
        candidates = [row for row in candidates if (row.get("easymaid_service_area") or "") == service_area]

    start = scheduled_start
    end = scheduled_end
    visit_date = start.split(" ")[0]
    available = []
    for row in candidates:
        employee = row["name"]

        has_shift = frappe.db.sql(
            """
            select name
            from `tabShift Assignment`
            where employee = %(employee)s
              and status = 'Active'
              and docstatus < 2
              and start_date <= %(visit_date)s
              and (end_date is null or end_date >= %(visit_date)s)
            limit 1
            """,
            {"employee": employee, "visit_date": visit_date},
            as_dict=True,
        )
        if not has_shift:
            continue

        overlap = frappe.db.sql(
            """
            select sv.name
            from `tabService Visit` sv
            inner join `tabCrew Assignment` ca on ca.parent = sv.name and ca.parenttype = 'Service Visit'
            where ca.employee = %(employee)s
              and sv.docstatus < 2
              and sv.status in ('Scheduled', 'In Progress')
              and sv.scheduled_start < %(scheduled_end)s
              and sv.scheduled_end > %(scheduled_start)s
            limit 1
            """,
            {
                "employee": employee,
                "scheduled_start": start,
                "scheduled_end": end,
            },
            as_dict=True,
        )
        if overlap:
            continue

        available.append(row)

    return {
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
        "service_area": service_area,
        "cleaners": available,
    }


@frappe.whitelist()
def mark_visit_status(visit_name: str, status: str, notes: str | None = None):
    visit = frappe.get_doc("Service Visit", visit_name)
    visit.status = status
    if status == "Completed" and not visit.completed_on:
        visit.completed_on = now_datetime()
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
    booking.service_address = _resolve_customer_address(so)
    booking.booking_type = booking_type
    booking.status = "Active"
    booking.sales_order = so.name
    if booking_type == "One-time":
        booking.scheduled_date = so.delivery_date or today()

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


@frappe.whitelist()
def generate_invoice_for_visit(visit_name: str):
    """Create a Sales Invoice for a completed one-time visit and link it back."""
    _ensure_owner_or_admin()

    visit = frappe.get_doc("Service Visit", visit_name)
    if visit.status != "Completed":
        frappe.throw(_("Only completed visits can be invoiced"))

    if visit.sales_invoice:
        return {"visit": visit.name, "sales_invoice": visit.sales_invoice, "created": False}

    booking = frappe.get_doc("Booking", visit.booking)
    if booking.booking_type != "One-time":
        frappe.throw(_("Use recurring billing workflow for recurring bookings"))

    if not booking.services:
        frappe.throw(_("Booking has no service items to invoice"))

    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "customer": booking.customer,
            "company": _default_company(),
            "due_date": add_days(today(), 7),
            "taxes_and_charges": _nj_tax_template(),
            "items": [
                {
                    "item_code": row.item_code,
                    "qty": row.qty or 1,
                    "rate": row.rate,
                }
                for row in booking.services
            ],
            "remarks": f"Generated from Service Visit {visit.name}",
        }
    )
    invoice.insert(ignore_permissions=True)
    invoice.run_method("calculate_taxes_and_totals")
    invoice.save(ignore_permissions=True)

    visit.sales_invoice = invoice.name
    visit.save(ignore_permissions=True)

    return {"visit": visit.name, "sales_invoice": invoice.name, "created": True}


@frappe.whitelist()
def ensure_recurring_billing_for_booking(booking_name: str):
    """Create recurring billing artifacts for a recurring booking.

    Strategy:
    - Ensure a Sales Order exists for the booking.
    - Ensure an Auto Repeat exists for monthly recurring invoice generation.
    """
    _ensure_owner_or_admin()

    booking = frappe.get_doc("Booking", booking_name)
    if booking.booking_type != "Recurring":
        frappe.throw(_("Booking must be Recurring to enable recurring billing"))
    if not booking.services:
        frappe.throw(_("Recurring booking has no service items"))

    sales_order_name = booking.sales_order
    if not sales_order_name:
        so_doc = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "customer": booking.customer,
                "customer_address": booking.service_address,
                "delivery_date": booking.start_date,
                "taxes_and_charges": _nj_tax_template(),
                "items": [
                    {
                        "item_code": row.item_code,
                        "qty": row.qty or 1,
                        "rate": row.rate,
                    }
                    for row in booking.services
                ],
                "remarks": f"Recurring source for Booking {booking.name}",
            }
        )
        so_doc.insert(ignore_permissions=True)
        booking.sales_order = so_doc.name
        booking.save(ignore_permissions=True)
        sales_order_name = so_doc.name

    auto_repeat_ref = frappe.db.get_value(
        "Auto Repeat",
        {
            "reference_doctype": "Sales Order",
            "reference_document": sales_order_name,
            "docstatus": ["<", 2],
        },
        "name",
    )
    if auto_repeat_ref:
        return {"booking": booking.name, "sales_order": sales_order_name, "auto_repeat": auto_repeat_ref}

    months = _frequency_to_months(booking.frequency or "Monthly", booking.interval or 1)
    auto_repeat = frappe.get_doc(
        {
            "doctype": "Auto Repeat",
            "reference_doctype": "Sales Order",
            "reference_document": sales_order_name,
            "frequency": "Monthly",
            "repeat_on_day": 1,
            "start_date": booking.start_date,
            "end_date": booking.end_date,
            "submit_on_creation": 1,
            "disabled": 0,
            "notify_by_email": 0,
            "period": months,
        }
    )
    auto_repeat.insert(ignore_permissions=True)

    return {
        "booking": booking.name,
        "sales_order": sales_order_name,
        "auto_repeat": auto_repeat.name,
    }


def _enforce_quote_request_throttle(limit_per_hour: int = 20):
    request_ip = getattr(frappe.local, "request_ip", None) or "unknown"
    hour_key = now_datetime().strftime("%Y-%m-%d-%H")
    key = f"easymaid:quote-request:{request_ip}:{hour_key}"
    cache = frappe.cache()
    count = cache.incr(key)
    if count == 1:
        cache.expire(key, 3600)

    if count > limit_per_hour:
        frappe.throw(_("Too many quote requests from this IP. Please try again later."))


@frappe.whitelist(allow_guest=True)
def submit_quote_request(payload: dict | None = None):
    """Create a Lead from the public Request a Quote flow with anti-spam checks."""
    _enforce_quote_request_throttle()
    payload = payload or frappe.form_dict

    try:
        cleaned = clean_quote_request_payload(payload)
    except ValueError as exc:
        frappe.throw(_(str(exc)))

    if cleaned["is_honeypot"]:
        # Return success to bots while dropping the submission.
        return {"ok": True, "lead": None, "ignored": True}

    lead = frappe.get_doc(
        {
            "doctype": "Lead",
            "lead_name": cleaned["full_name"],
            "email_id": cleaned["email"],
            "mobile_no": cleaned["phone"],
            "source": "Website",
            "status": "Lead",
            "notes": [
                {"note": f"Address: {cleaned['address']}<br><br>Request: {cleaned['details']}"}
            ],
            "city": cleaned["city"],
            "state": cleaned["state"],
        }
    )
    lead.insert(ignore_permissions=True)

    return {"ok": True, "lead": lead.name, "ignored": False}


@frappe.whitelist()
def current_portal_role():
    """Return current user + one supported Easy Maid role for SPA route guards."""
    user = frappe.session.user
    if not user or user == "Guest":
        return {"authenticated": False, "role": None, "user": "Guest"}

    role_priority = ["Easy Maid Owner", "Easy Maid Client", "Easy Maid Cleaner"]
    user_roles = set(frappe.get_roles(user))
    matched = next((role for role in role_priority if role in user_roles), None)

    return {
        "authenticated": True,
        "user": user,
        "role": matched,
    }


@frappe.whitelist()
def qualify_lead_to_opportunity(lead_name: str):
    """Convert a qualified Lead to Opportunity using ERPNext mapping."""
    _ensure_owner_or_admin()
    mapper = _get_mapper([
        "erpnext.crm.doctype.lead.lead.make_opportunity",
    ])
    opp_doc = mapper(lead_name)

    if isinstance(opp_doc, dict):
        opp_doc = frappe.get_doc(opp_doc)
    if not opp_doc.get("company"):
        opp_doc.company = _default_company()
    if opp_doc.docstatus == 0 and not opp_doc.name:
        opp_doc.insert(ignore_permissions=True)

    return {"opportunity": opp_doc.name, "lead": lead_name}


@frappe.whitelist()
def create_quotation_from_opportunity(
    opportunity_name: str,
    items: str | list[dict] | None = None,
    tax_template: str | None = None,
):
    """Create a quotation from an Opportunity and append service items."""
    _ensure_owner_or_admin()

    mapper = _get_mapper([
        "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
    ])
    q_doc = mapper(opportunity_name)
    if isinstance(q_doc, dict):
        q_doc = frappe.get_doc(q_doc)

    for row in _normalize_items(items):
        q_doc.append(
            "items",
            {
                "item_code": row.get("item_code"),
                "qty": row.get("qty", 1),
                "rate": row.get("rate"),
            },
        )

    template = tax_template or _nj_tax_template()
    if template:
        q_doc.taxes_and_charges = template
    if not q_doc.get("company"):
        q_doc.company = _default_company()

    q_doc.insert(ignore_permissions=True)
    q_doc.run_method("calculate_taxes_and_totals")
    q_doc.save(ignore_permissions=True)

    return {
        "quotation": q_doc.name,
        "grand_total": q_doc.grand_total,
        "taxes_and_charges": q_doc.taxes_and_charges,
    }


@frappe.whitelist()
def send_quotation_email(quotation_name: str, recipient_email: str | None = None):
    """Send quotation using ERPNext's built-in email print flow."""
    _ensure_owner_or_admin()

    quotation = frappe.get_doc("Quotation", quotation_name)
    recipient = recipient_email or quotation.contact_email
    if not recipient:
        frappe.throw(_("Recipient email is required to send quotation"))

    print_format = "Easy Maid Quotation" if frappe.db.exists("Print Format", "Easy Maid Quotation") else quotation.meta.default_print_format

    frappe.sendmail(
        recipients=[recipient],
        subject=_("Quotation {0} from Maidurday Cleaning Service").format(quotation.name),
        message=_("Please find your quotation attached."),
        reference_doctype="Quotation",
        reference_name=quotation.name,
        print_format=print_format,
        attachments=[frappe.attach_print("Quotation", quotation.name)],
    )

    return {"quotation": quotation.name, "sent_to": recipient}


@frappe.whitelist()
def convert_quotation_to_sales_order_and_booking(quotation_name: str, booking_type: str = "One-time"):
    """Convert accepted quotation to Sales Order and seed Booking record."""
    _ensure_owner_or_admin()

    quotation = frappe.get_doc("Quotation", quotation_name)
    if quotation.docstatus == 0:
        quotation.submit()

    mapper = _get_mapper([
        "erpnext.selling.doctype.quotation.quotation.make_sales_order",
    ])
    so_doc = mapper(quotation.name)
    if isinstance(so_doc, dict):
        so_doc = frappe.get_doc(so_doc)
    if not so_doc.get("company"):
        so_doc.company = _default_company()
    if not so_doc.get("delivery_date"):
        so_doc.delivery_date = add_days(today(), 7)
    so_doc.insert(ignore_permissions=True)

    booking_name = create_booking_from_sales_order(so_doc.name, booking_type=booking_type)
    return {
        "sales_order": so_doc.name,
        "booking": booking_name,
        "quotation": quotation_name,
    }


@frappe.whitelist()
def owner_dashboard_metrics():
    _ensure_owner_or_admin()
    open_visits = frappe.db.count("Service Visit", {"status": ["in", ["Scheduled", "In Progress"]]})
    unassigned = frappe.db.sql(
        """
        select count(*)
        from `tabService Visit` sv
        where sv.status in ('Scheduled', 'In Progress')
          and not exists (
              select 1 from `tabCrew Assignment` ca where ca.parent = sv.name and ca.parenttype = 'Service Visit'
          )
        """,
    )[0][0]
    ar_total = frappe.db.sql(
        """
        select coalesce(sum(grand_total), 0)
        from `tabSales Invoice`
        where docstatus = 1 and outstanding_amount > 0
        """,
    )[0][0]
    return {
        "upcoming_visits": open_visits,
        "unassigned_visits": int(unassigned or 0),
        "accounts_receivable": float(ar_total or 0),
    }


@frappe.whitelist()
def client_portal_snapshot():
    _ensure_client_or_owner()
    customer = _current_customer()
    roles = _current_user_roles()
    if not customer and roles.isdisjoint({"System Manager", "Easy Maid Owner"}):
        frappe.throw(_("No customer profile mapped to this user"))

    filters = {"customer": customer} if customer else {}
    bookings = frappe.get_all(
        "Booking",
        filters=filters,
        fields=["name", "status", "booking_type", "scheduled_date", "start_date", "end_date"],
        order_by="modified desc",
        limit_page_length=20,
    )
    visits = frappe.get_all(
        "Service Visit",
        filters=filters,
        fields=["name", "booking", "status", "scheduled_start", "scheduled_end"],
        order_by="scheduled_start asc",
        limit_page_length=20,
    )
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer} if customer else {},
        fields=["name", "posting_date", "grand_total", "outstanding_amount", "status"],
        order_by="posting_date desc",
        limit_page_length=20,
    )
    return {
        "customer": customer,
        "bookings": bookings,
        "visits": visits,
        "invoices": invoices,
    }


@frappe.whitelist()
def client_create_booking(
    service_address: str,
    booking_type: str,
    scheduled_date: str | None = None,
    frequency: str | None = None,
    interval: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
    services: str | list[dict] | None = None,
):
    _ensure_client_or_owner()
    customer = _current_customer()
    if not customer:
        frappe.throw(_("No customer profile mapped to this user"))
    if not service_address:
        frappe.throw(_("Service address is required"))

    booking = frappe.new_doc("Booking")
    booking.customer = customer
    booking.service_address = service_address
    booking.booking_type = booking_type
    booking.status = "Active"
    booking.scheduled_date = scheduled_date
    booking.frequency = frequency
    booking.interval = interval
    booking.start_date = start_date
    booking.end_date = end_date

    normalized = _normalize_items(services)
    if not normalized:
        frappe.throw(_("At least one service item is required"))

    for row in normalized:
        booking.append(
            "services",
            {
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name"),
                "qty": row.get("qty", 1),
                "rate": row.get("rate"),
                "amount": row.get("amount") or ((row.get("qty", 1) or 1) * (row.get("rate") or 0)),
            },
        )

    booking.insert(ignore_permissions=True)
    return {"booking": booking.name}


@frappe.whitelist()
def cleaner_today_jobs():
    roles = _current_user_roles()
    if roles.isdisjoint({"Easy Maid Cleaner", "Cleaner", "Employee", "System Manager", "Easy Maid Owner"}):
        frappe.throw(_("Only cleaners or owners can view cleaner jobs"))

    employee = _current_employee()
    if not employee and roles.isdisjoint({"System Manager", "Easy Maid Owner"}):
        frappe.throw(_("No employee profile mapped to this user"))

    start = f"{today()} 00:00:00"
    end = f"{today()} 23:59:59"
    filters = {"scheduled_start": ["between", [start, end]]}
    jobs = frappe.get_all(
        "Service Visit",
        filters=filters,
        fields=["name", "booking", "customer", "status", "scheduled_start", "scheduled_end"],
        order_by="scheduled_start asc",
    )

    if employee:
        assigned = {
            row.parent
            for row in frappe.get_all(
                "Crew Assignment",
                filters={"parenttype": "Service Visit", "employee": employee},
                fields=["parent"],
            )
        }
        jobs = [job for job in jobs if job["name"] in assigned]

    return {"employee": employee, "jobs": jobs}


@frappe.whitelist()
def create_invoice_payment_request(invoice_name: str):
    """Create/reuse an ERPNext Payment Request for an unpaid Sales Invoice."""
    _ensure_client_or_owner()

    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    roles = _current_user_roles()
    customer = _current_customer()
    if roles.isdisjoint({"System Manager", "Easy Maid Owner"}) and invoice.customer != customer:
        frappe.throw(_("You can only pay your own invoices"))

    if float(invoice.outstanding_amount or 0) <= 0:
        return {
            "invoice": invoice.name,
            "status": "Paid",
            "payment_request": None,
            "payment_url": None,
        }

    existing = frappe.db.get_value(
        "Payment Request",
        {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "docstatus": ["<", 2],
            "status": ["in", ["Initiated", "Requested", "Paid", "Partially Paid"]],
        },
        "name",
    )

    if existing:
        pr_doc = frappe.get_doc("Payment Request", existing)
    else:
        pr_doc = frappe.get_doc(
            {
                "doctype": "Payment Request",
                "payment_request_type": "Inward",
                "party_type": "Customer",
                "party": invoice.customer,
                "company": invoice.company,
                "currency": invoice.currency,
                "grand_total": invoice.outstanding_amount,
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice.name,
                "subject": _("Invoice payment for {0}").format(invoice.name),
                "message": _("Please complete your payment securely via Stripe hosted checkout."),
                "mute_email": 1,
            }
        )
        pr_doc.insert(ignore_permissions=True)

    try:
        payment_url = pr_doc.get_payment_url()
    except Exception:
        payment_url = f"/payments?doctype=Sales%20Invoice&docname={invoice.name}"

    return {
        "invoice": invoice.name,
        "status": invoice.status,
        "outstanding_amount": float(invoice.outstanding_amount or 0),
        "payment_request": pr_doc.name,
        "payment_url": payment_url,
    }


@frappe.whitelist()
def reconcile_invoice_payment(
    invoice_name: str,
    paid_amount: float | None = None,
    reference_no: str | None = None,
    reference_date: str | None = None,
):
    """Create and submit Payment Entry for invoice reconciliation.

    Intended for payment-webhook success handling (Stripe hosted checkout).
    """
    _ensure_owner_or_admin()

    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    outstanding = float(invoice.outstanding_amount or 0)
    if outstanding <= 0:
        return {
            "invoice": invoice.name,
            "status": invoice.status,
            "payment_entry": None,
            "created": False,
            "reason": "Invoice already paid",
        }

    amount = min(float(paid_amount or outstanding), outstanding)

    get_payment_entry = _get_mapper([
        "erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
    ])
    pe = get_payment_entry("Sales Invoice", invoice.name, party_amount=amount)
    if isinstance(pe, dict):
        pe = frappe.get_doc(pe)

    pe.reference_no = reference_no or f"stripe-{frappe.generate_hash(length=10)}"
    pe.reference_date = reference_date or today()
    pe.remarks = f"Payment reconciliation for {invoice.name}"
    pe.insert(ignore_permissions=True)
    pe.submit()

    invoice.reload()
    return {
        "invoice": invoice.name,
        "status": invoice.status,
        "outstanding_amount": float(invoice.outstanding_amount or 0),
        "payment_entry": pe.name,
        "created": True,
    }


@frappe.whitelist()
def invoice_payment_status(invoice_name: str):
    """Return payment status details for client retry flow."""
    _ensure_client_or_owner()

    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    roles = _current_user_roles()
    customer = _current_customer()
    if roles.isdisjoint({"System Manager", "Easy Maid Owner"}) and invoice.customer != customer:
        frappe.throw(_("You can only view your own invoices"))

    return {
        "invoice": invoice.name,
        "status": invoice.status,
        "grand_total": float(invoice.grand_total or 0),
        "outstanding_amount": float(invoice.outstanding_amount or 0),
        "paid": float(invoice.outstanding_amount or 0) <= 0,
    }


@frappe.whitelist()
def owner_financial_snapshot(from_date: str | None = None, to_date: str | None = None):
    """Return high-level AR, income, and GL counts for owner bookkeeping visibility."""
    _ensure_owner_or_admin()

    filters = ["docstatus = 1"]
    params: dict[str, str] = {}
    if from_date:
        filters.append("posting_date >= %(from_date)s")
        params["from_date"] = from_date
    if to_date:
        filters.append("posting_date <= %(to_date)s")
        params["to_date"] = to_date
    where = " and ".join(filters)

    ar = frappe.db.sql(
        f"""
        select coalesce(sum(outstanding_amount), 0) as ar_total,
               count(name) as open_invoices
        from `tabSales Invoice`
        where {where} and outstanding_amount > 0
        """,
        params,
        as_dict=True,
    )[0]

    revenue = frappe.db.sql(
        f"""
        select coalesce(sum(base_net_total), 0) as net_revenue,
               coalesce(sum(base_grand_total), 0) as gross_revenue
        from `tabSales Invoice`
        where {where}
        """,
        params,
        as_dict=True,
    )[0]

    gl_entries = frappe.db.sql(
        """
        select count(name) as gl_count
        from `tabGL Entry`
        where posting_date >= %(from_date)s and posting_date <= %(to_date)s
        """,
        {
            "from_date": from_date or "1900-01-01",
            "to_date": to_date or today(),
        },
        as_dict=True,
    )[0]

    return {
        "from_date": from_date,
        "to_date": to_date,
        "accounts_receivable": float(ar.get("ar_total") or 0),
        "open_invoices": int(ar.get("open_invoices") or 0),
        "net_revenue": float(revenue.get("net_revenue") or 0),
        "gross_revenue": float(revenue.get("gross_revenue") or 0),
        "gl_entries": int(gl_entries.get("gl_count") or 0),
    }


@frappe.whitelist()
def client_invoice_receipt_url(invoice_name: str):
    """Return a printable receipt URL for a paid invoice."""
    _ensure_client_or_owner()
    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    roles = _current_user_roles()
    customer = _current_customer()
    if roles.isdisjoint({"System Manager", "Easy Maid Owner"}) and invoice.customer != customer:
        frappe.throw(_("You can only access receipts for your own invoices"))

    if float(invoice.outstanding_amount or 0) > 0:
        frappe.throw(_("Invoice is not paid yet"))

    print_format = "Easy Maid Receipt" if frappe.db.exists("Print Format", "Easy Maid Receipt") else "Standard"
    url = (
        "/api/method/frappe.utils.print_format.download_pdf"
        f"?doctype=Sales%20Invoice&name={invoice.name}&format={print_format}&no_letterhead=0"
    )
    return {"invoice": invoice.name, "receipt_url": url}


# ---------------------------------------------------------------------------
# Stripe webhook (task 12.3)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def stripe_webhook():
    """Receive Stripe webhook events and reconcile payments.

    Verifies the Stripe-Signature header against the webhook secret stored in
    site config key `stripe_webhook_secret`. Card data is never sent here —
    Stripe only sends event metadata. Reconciliation is idempotent (a paid
    invoice is skipped on retry).
    """
    import hashlib
    import hmac

    request = frappe.request
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = frappe.conf.get("stripe_webhook_secret", "")

    if webhook_secret:
        # Verify Stripe signature: t=timestamp,v1=computed_hmac
        try:
            parts = {k: v for part in sig_header.split(",") for k, v in [part.split("=", 1)]}
            timestamp = parts.get("t", "")
            expected = hmac.new(
                webhook_secret.encode(),
                f"{timestamp}.{payload}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, parts.get("v1", "")):
                frappe.throw(_("Stripe webhook signature verification failed"), frappe.AuthenticationError)
        except (ValueError, KeyError):
            frappe.throw(_("Invalid Stripe webhook signature format"), frappe.AuthenticationError)

    try:
        event = frappe.parse_json(payload)
    except Exception:
        frappe.throw(_("Invalid Stripe webhook payload"))

    event_type = event.get("type", "")
    data_object = (event.get("data") or {}).get("object") or {}

    if event_type in ("payment_intent.succeeded", "checkout.session.completed"):
        amount_received = data_object.get("amount_received") or data_object.get("amount_total") or 0
        paid_amount = round(float(amount_received) / 100, 2)  # Stripe amounts in cents
        reference_no = data_object.get("id", "")
        metadata = data_object.get("metadata") or {}
        invoice_name = metadata.get("invoice_name") or metadata.get("frappe_invoice")

        if invoice_name and paid_amount > 0:
            try:
                result = reconcile_invoice_payment(
                    invoice_name=invoice_name,
                    paid_amount=paid_amount,
                    reference_no=reference_no,
                )
                frappe.logger().info(f"Stripe webhook: reconciled invoice {invoice_name}: {result}")
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Easy Maid: Stripe webhook reconcile failed for {invoice_name}")

    return {"ok": True, "event_type": event_type}


# ---------------------------------------------------------------------------
# Self-service signup + online booking (tasks 17.1–17.6)
# ---------------------------------------------------------------------------

def _enforce_signup_throttle(limit_per_hour: int = 5):
    request_ip = getattr(frappe.local, "request_ip", None) or "unknown"
    hour_key = now_datetime().strftime("%Y-%m-%d-%H")
    key = f"easymaid:signup:{request_ip}:{hour_key}"
    cache = frappe.cache()
    count = cache.incr(key)
    if count == 1:
        cache.expire(key, 3600)
    if count > limit_per_hour:
        frappe.throw(_("Too many signup attempts from this IP. Please try again later."))


@frappe.whitelist(allow_guest=True)
def register_client(full_name: str, email: str, password: str):
    """Create a portal User (client role) + linked Customer for self-service signup.

    Frappe's `send_welcome_email=1` sends a verification link so the email is
    confirmed before the account is usable for booking.
    """
    _enforce_signup_throttle()

    if not full_name or not full_name.strip():
        frappe.throw(_("Full name is required"))
    if not email or "@" not in email:
        frappe.throw(_("A valid email address is required"))
    if not password or len(password) < 8:
        frappe.throw(_("Password must be at least 8 characters"))

    if frappe.db.exists("User", email):
        frappe.throw(_("An account with this email already exists. Please log in."))

    parts = full_name.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "user_type": "Website User",
        "send_welcome_email": 1,
        "roles": [{"role": "Easy Maid Client"}],
    })
    user.new_password = password
    user.insert(ignore_permissions=True)

    # Create linked Customer scoped to this user (email_id = lookup key used by _current_customer)
    customer_group = "Residential"
    if not frappe.db.exists("Customer Group", customer_group):
        customer_group = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Individual"

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": full_name.strip(),
        "customer_type": "Individual",
        "customer_group": customer_group,
        "email_id": email,
        "territory": "United States",
    })
    customer.insert(ignore_permissions=True)

    return {"ok": True, "message": _("Account created. Check your email to verify your address before booking.")}


@frappe.whitelist(allow_guest=True)
def get_booking_estimate(items: str | list | None = None):
    """Return an itemized price estimate including NJ sales tax (6.625%).

    The server always recomputes prices from the ERPNext Price List — the
    client must NEVER supply amounts that are trusted for billing.

    items: JSON array of {item_code, qty} objects.
    """
    import json as _json

    raw = items or frappe.form_dict.get("items")
    if isinstance(raw, str):
        try:
            raw = _json.loads(raw)
        except Exception:
            frappe.throw(_("items must be a JSON array of {item_code, qty}"))
    if not raw or not isinstance(raw, list):
        frappe.throw(_("At least one item is required"))

    NJ_TAX_RATE = 6.625  # percentage; source of truth is the NJ Sales Tax template

    # Attempt to read the live rate from the configured tax template
    try:
        tax_name = frappe.db.get_value(
            "Sales Taxes and Charges Template", {"title": "NJ Sales Tax"}, "name"
        )
        if tax_name:
            live_rate = frappe.db.get_value(
                "Sales Taxes and Charges",
                {"parent": tax_name},
                "rate",
            )
            if live_rate:
                NJ_TAX_RATE = float(live_rate)
    except Exception:
        pass

    line_items = []
    subtotal = 0.0

    for entry in raw:
        item_code = (entry.get("item_code") or "").strip()
        qty = max(float(entry.get("qty") or 1), 0)
        if not item_code:
            continue

        rate = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": "Standard Selling"},
            "price_list_rate",
        )
        if rate is None:
            frappe.throw(_("Item {0} is not in the price list or does not exist").format(item_code))

        rate = float(rate)
        amount = round(rate * qty, 2)
        subtotal += amount

        item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
        line_items.append({"item_code": item_code, "item_name": item_name, "qty": qty, "rate": rate, "amount": amount})

    tax_amount = round(subtotal * NJ_TAX_RATE / 100, 2)
    grand_total = round(subtotal + tax_amount, 2)

    return {
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "tax_rate": NJ_TAX_RATE,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "currency": "USD",
    }


@frappe.whitelist()
def submit_online_booking(
    service_address: str,
    booking_type: str,
    services: str | list | None = None,
    scheduled_date: str | None = None,
    frequency: str | None = None,
    interval: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
    pay_now: bool = False,
):
    """Self-service online booking: create Booking + first Visit, optionally prepay.

    Price is always recomputed SERVER-SIDE from the Price List to prevent
    client-side tampering. Requires an authenticated user with Easy Maid Client
    role or higher.
    """
    _ensure_client_or_owner()
    customer = _current_customer()
    if not customer:
        frappe.throw(_("No customer profile found. Please complete your account setup."))

    if not service_address:
        frappe.throw(_("Service address is required"))
    if booking_type == "One-time" and not scheduled_date:
        frappe.throw(_("A scheduled date is required for one-time bookings"))
    if booking_type == "Recurring" and not start_date:
        frappe.throw(_("A start date is required for recurring bookings"))

    normalized = _normalize_items(services)
    if not normalized:
        frappe.throw(_("At least one service item is required"))

    # Server-side price recomputation — never trust client-supplied amounts
    estimate = get_booking_estimate(items=normalized)
    item_lookup = {li["item_code"]: li for li in estimate["line_items"]}

    booking = frappe.new_doc("Booking")
    booking.customer = customer
    booking.service_address = service_address
    booking.booking_type = booking_type
    booking.status = "Active"
    booking.scheduled_date = scheduled_date
    booking.frequency = frequency
    booking.interval = interval
    booking.start_date = start_date
    booking.end_date = end_date

    for row in normalized:
        item_code = (row.get("item_code") or "").strip()
        if item_code not in item_lookup:
            frappe.throw(_("Item {0} not found in price list").format(item_code))
        li = item_lookup[item_code]
        booking.append("services", {
            "item_code": item_code,
            "item_name": li["item_name"],
            "qty": li["qty"],
            "rate": li["rate"],
            "amount": li["amount"],
        })

    booking.insert(ignore_permissions=True)

    payment_url = None
    if pay_now:
        # Generate a Sales Invoice and create a Stripe Payment Request
        try:
            invoice = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": customer,
                "company": _default_company(),
                "due_date": add_days(today(), 1),
                "taxes_and_charges": _nj_tax_template(),
                "items": [
                    {"item_code": row.item_code, "qty": row.qty, "rate": row.rate}
                    for row in booking.services
                ],
                "remarks": f"Online booking payment for {booking.name}",
            })
            invoice.insert(ignore_permissions=True)
            invoice.run_method("calculate_taxes_and_totals")
            invoice.submit()
            pr_result = create_invoice_payment_request(invoice.name)
            payment_url = pr_result.get("payment_url")
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Easy Maid: prepay invoice creation failed for {booking.name}")

    return {
        "booking": booking.name,
        "estimate": estimate,
        "pay_now": pay_now,
        "payment_url": payment_url,
    }


@frappe.whitelist(allow_guest=True)
def check_service_area(city: str, state: str = "NJ") -> dict:
    """Return whether a given city/state is in our serviceable area.

    If not, the caller should route the visitor to Request a Quote (Lead) flow.
    """
    SERVICEABLE_NJ_CITIES = {
        "montclair", "bloomfield", "maplewood", "south orange", "livingston",
        "west orange", "millburn", "short hills", "hoboken", "jersey city",
        "bayonne", "weehawken", "north bergen", "hackensack", "paramus",
        "ridgewood", "teaneck", "fort lee", "summit", "westfield", "cranford",
        "clark", "scotch plains", "new brunswick", "edison", "woodbridge",
        "east brunswick", "old bridge", "morristown", "parsippany", "denville",
        "madison",
    }
    city_lower = (city or "").strip().lower()
    in_area = state.strip().upper() == "NJ" and city_lower in SERVICEABLE_NJ_CITIES
    return {"in_service_area": in_area, "city": city, "state": state}

