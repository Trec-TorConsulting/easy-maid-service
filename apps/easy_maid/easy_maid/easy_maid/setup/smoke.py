from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, today

from easy_maid.easy_maid import api
from easy_maid.easy_maid import permissions


@frappe.whitelist()
def run_lead_to_booking_smoke(customer_email: str = "quote-smoke@example.com"):
    """Runtime smoke path for 11.x using native ERPNext mappers.

    This is intended for a non-production smoke check and is idempotent by name prefix.
    """
    lead_name = _create_or_get_smoke_lead(customer_email)
    opp = api.qualify_lead_to_opportunity(lead_name)["opportunity"]

    quotation = api.create_quotation_from_opportunity(
        opp,
        items=[
            {"item_code": "EMS-STD-CLEAN", "qty": 1, "rate": 150},
        ],
        tax_template="NJ Sales Tax",
    )["quotation"]

    frappe.db.set_value("Quotation", quotation, "status", "Open")

    converted = api.convert_quotation_to_sales_order_and_booking(quotation, booking_type="One-time")

    quote_doc = frappe.get_doc("Quotation", quotation)
    checks = {
        "quotation_has_items": bool(quote_doc.items),
        "quotation_grand_total_positive": float(quote_doc.grand_total or 0) > 0,
        "quotation_taxes_present": bool(quote_doc.taxes_and_charges),
    }

    return {
        "lead": lead_name,
        "opportunity": opp,
        "quotation": quotation,
        "sales_order": converted["sales_order"],
        "booking": converted["booking"],
        "checks": checks,
    }


@frappe.whitelist()
def run_payroll_smoke(employee: str, from_date: str | None = None, to_date: str | None = None):
    """Best-effort payroll smoke: assign structure and create a test salary slip.

    Returns status details without raising for optional/missing payroll doctypes.
    """
    result = {
        "employee": employee,
        "assignment": None,
        "salary_slip": None,
        "submitted": False,
        "skipped": False,
        "reason": None,
    }

    required = ["Salary Structure", "Salary Structure Assignment", "Salary Slip"]
    for doctype in required:
        if not frappe.db.exists("DocType", doctype):
            result["skipped"] = True
            result["reason"] = f"Missing doctype: {doctype}"
            return result

    structure = frappe.db.get_value("Salary Structure", "Easy Maid Cleaner Monthly", "name")
    if not structure:
        result["skipped"] = True
        result["reason"] = "Salary Structure Easy Maid Cleaner Monthly not found"
        return result

    start = getdate(from_date) if from_date else getdate(today()).replace(day=1)
    end = getdate(to_date) if to_date else add_days(start, 29)

    assignment_name = frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "salary_structure": structure,
            "from_date": ["<=", start],
            "docstatus": ["<", 2],
        },
        "name",
    )
    if not assignment_name:
        assignment = frappe.get_doc(
            {
                "doctype": "Salary Structure Assignment",
                "employee": employee,
                "salary_structure": structure,
                "from_date": start,
                "base": 2950,
                "company": "Easy Maid Service",
            }
        )
        assignment.insert(ignore_permissions=True)
        assignment_name = assignment.name
    result["assignment"] = assignment_name

    slip_name = frappe.db.get_value(
        "Salary Slip",
        {
            "employee": employee,
            "start_date": start,
            "end_date": end,
            "docstatus": ["<", 2],
        },
        "name",
    )
    if slip_name:
        slip = frappe.get_doc("Salary Slip", slip_name)
    else:
        slip = frappe.get_doc(
            {
                "doctype": "Salary Slip",
                "employee": employee,
                "start_date": start,
                "end_date": end,
                "payroll_frequency": "Monthly",
                "company": "Easy Maid Service",
                "salary_structure": structure,
            }
        )
        slip.insert(ignore_permissions=True)

    result["salary_slip"] = slip.name
    if slip.docstatus == 0:
        try:
            slip.submit()
            result["submitted"] = True
        except Exception:
            result["submitted"] = False
            result["reason"] = "Salary slip created but submit failed; check payroll dependencies"

    return result


@frappe.whitelist()
def run_capability_smoke_summary():
    """Summarize key API smoke checks for 11.x/12.x/13.x/14.x."""
    summary = {
        "owner_metrics": None,
        "owner_finance": None,
        "lead_quote_flow": None,
        "invoice_payment_request": None,
        "permission_scope": None,
        "payment_reconciliation": None,
        "status": "ok",
        "errors": [],
    }

    try:
        summary["owner_metrics"] = api.owner_dashboard_metrics()
    except Exception:
        summary["status"] = "partial"
        summary["errors"].append("owner_dashboard_metrics failed")

    try:
        summary["owner_finance"] = api.owner_financial_snapshot()
    except Exception:
        summary["status"] = "partial"
        summary["errors"].append("owner_financial_snapshot failed")

    try:
        summary["permission_scope"] = run_permission_scope_smoke()
    except Exception:
        summary["status"] = "partial"
        summary["errors"].append("run_permission_scope_smoke failed")

    try:
        summary["lead_quote_flow"] = run_lead_to_booking_smoke()
    except Exception:
        summary["status"] = "partial"
        summary["errors"].append("run_lead_to_booking_smoke failed")

    try:
        completed_visit = frappe.db.get_value(
            "Service Visit",
            {"status": "Completed", "sales_invoice": ["is", "not set"]},
            "name",
            order_by="modified desc",
        )
        if completed_visit:
            invoice_result = api.generate_invoice_for_visit(completed_visit)
            payment_result = api.create_invoice_payment_request(invoice_result["sales_invoice"])
            summary["invoice_payment_request"] = {
                "visit": completed_visit,
                "sales_invoice": invoice_result.get("sales_invoice"),
                "payment_request": payment_result.get("payment_request"),
                "payment_url": payment_result.get("payment_url"),
            }

            try:
                reconcile = api.reconcile_invoice_payment(invoice_result["sales_invoice"])
                summary["payment_reconciliation"] = reconcile
            except Exception:
                summary["status"] = "partial"
                summary["errors"].append("payment reconciliation smoke failed")
        else:
            summary["invoice_payment_request"] = {
                "skipped": True,
                "reason": "No completed uninvoiced Service Visit found",
            }
            summary["payment_reconciliation"] = {
                "skipped": True,
                "reason": "No completed uninvoiced Service Visit found",
            }
    except Exception:
        summary["status"] = "partial"
        summary["errors"].append("invoice/payment request smoke failed")

    return summary


@frappe.whitelist()
def run_permission_scope_smoke(cleaner_user: str | None = None, owner_user: str = "Administrator"):
    """Return permission query snapshots for least-privilege verification."""
    cleaner_user = cleaner_user or frappe.db.get_value(
        "Employee", {"designation": ["in", ["Cleaner", "Lead Cleaner"]]}, "user_id"
    )
    if not cleaner_user:
        return {
            "skipped": True,
            "reason": "No cleaner user found",
        }

    cleaner_employee = frappe.db.get_value("Employee", {"user_id": cleaner_user}, "name")
    owner_queries = {
        "employee_query": permissions.employee_query(owner_user),
        "salary_slip_query": permissions.salary_slip_query(owner_user),
    }
    cleaner_queries = {
        "employee_query": permissions.employee_query(cleaner_user),
        "salary_slip_query": permissions.salary_slip_query(cleaner_user),
    }

    return {
        "cleaner_user": cleaner_user,
        "cleaner_employee": cleaner_employee,
        "owner_queries": owner_queries,
        "cleaner_queries": cleaner_queries,
        "checks": {
            "owner_has_full_access": owner_queries["employee_query"] == "1=1" and owner_queries["salary_slip_query"] == "1=1",
            "cleaner_is_scoped": (cleaner_employee or "") in cleaner_queries["employee_query"]
            and (cleaner_employee or "") in cleaner_queries["salary_slip_query"],
        },
    }


@frappe.whitelist()
def run_task_evidence_matrix(cleaner_user: str | None = None, payroll_employee: str | None = None):
    """Return runtime evidence status for unresolved implementation tasks.

    Status values:
    - PASS: evidence check succeeded
    - PARTIAL: check ran but not fully satisfied
    - MANUAL: requires external/manual validation
    """
    matrix: dict[str, dict] = {}

    def record(task_id: str, status: str, evidence: str, detail: dict | None = None):
        matrix[task_id] = {
            "status": status,
            "evidence": evidence,
            "detail": detail or {},
        }

    # 11.1 native quote intake
    has_web_form = bool(frappe.db.exists("Web Form", "Request a Quote"))
    record("11.1", "PASS" if has_web_form else "PARTIAL", "Web Form Request a Quote exists", {"exists": has_web_form})

    # 11.2 + 11.3 lead->quote->sales order path and branded quote format
    try:
        flow = run_lead_to_booking_smoke()
        flow_ok = all(flow.get("checks", {}).values())
        record("11.2", "PASS" if flow_ok else "PARTIAL", "Lead to Booking smoke flow executed", flow)
    except Exception as exc:
        record("11.2", "PARTIAL", f"Lead to Booking smoke failed: {exc}")

    has_quote_pf = bool(frappe.db.exists("Print Format", "Easy Maid Quotation"))
    record(
        "11.3",
        "PASS" if has_quote_pf else "PARTIAL",
        "Branded quotation print format exists",
        {"print_format": "Easy Maid Quotation", "exists": has_quote_pf},
    )

    # 12.3 Stripe gateway runtime validation
    stripe_enabled = False
    if frappe.db.exists("DocType", "Stripe Settings"):
        stripe = frappe.get_single("Stripe Settings")
        stripe_enabled = bool(getattr(stripe, "enabled", 0) and getattr(stripe, "publishable_key", None) and getattr(stripe, "secret_key", None))
    record(
        "12.3",
        "PASS" if stripe_enabled else "PARTIAL",
        "Stripe settings configured (hosted checkout readiness)",
        {"configured": stripe_enabled},
    )

    # 12.5 bookkeeping + branded receipt format presence
    try:
        finance = api.owner_financial_snapshot()
        has_receipt_pf = bool(frappe.db.exists("Print Format", "Easy Maid Receipt"))
        status = "PASS" if has_receipt_pf else "PARTIAL"
        record("12.5", status, "Financial snapshot and receipt format check", {"finance": finance, "has_receipt_print_format": has_receipt_pf})
    except Exception as exc:
        record("12.5", "PARTIAL", f"Financial snapshot check failed: {exc}")

    # 13.3 payroll smoke (requires at least one employee)
    payroll_employee = payroll_employee or frappe.db.get_value(
        "Employee", {"designation": ["in", ["Cleaner", "Lead Cleaner"]]}, "name"
    )
    if payroll_employee:
        payroll = run_payroll_smoke(payroll_employee)
        payroll_pass = bool(payroll.get("salary_slip"))
        record("13.3", "PASS" if payroll_pass else "PARTIAL", "Payroll smoke result", payroll)
    else:
        record("13.3", "PARTIAL", "No employee available for payroll smoke")

    # 13.4 + 15.2 least-privilege scope checks
    scope = run_permission_scope_smoke(cleaner_user=cleaner_user)
    scope_pass = bool(scope.get("checks", {}).get("cleaner_is_scoped"))
    record("13.4", "PASS" if scope_pass else "PARTIAL", "Cleaner payroll/data scope check", scope)
    record("15.2", "PASS" if scope_pass else "PARTIAL", "Least-privilege scope check", scope)

    # 15.5 capability smoke end-to-end within app boundary
    cap = run_capability_smoke_summary()
    cap_pass = cap.get("status") == "ok"
    record("15.5", "PASS" if cap_pass else "PARTIAL", "Consolidated capability smoke summary", cap)

    # 15.6 existing external frappe instance unaffected requires external assertion
    record(
        "15.6",
        "MANUAL",
        "Requires external namespace/site validation outside easymaid app context",
        {"note": "Run namespace/site checks and external HTTP probes manually"},
    )

    return matrix


@frappe.whitelist()
def create_or_get_mock_unpaid_invoice(customer_name: str | None = None):
    """Return an unpaid Sales Invoice, creating one if none exists.

    Used for Stripe hosted-checkout runtime smoke where an unpaid invoice is required.
    """
    existing = frappe.db.get_value(
        "Sales Invoice",
        {
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "status": ["not in", ["Paid", "Cancelled"]],
        },
        "name",
        order_by="posting_date desc, modified desc",
    )
    if existing:
        return {"sales_invoice": existing, "created": False}

    company = frappe.db.get_value("Company", {"company_name": "Easy Maid Service"}, "name") or frappe.db.get_value(
        "Company", {}, "name"
    )
    if not company:
        frappe.throw("No Company found. Run bootstrap first.")

    company_currency = frappe.db.get_value("Company", company, "default_currency") or "USD"

    customer = customer_name or frappe.db.get_value("Customer", {}, "name")
    if not customer:
        territory = frappe.db.get_value("Territory", "All Territories", "name")
        if not territory:
            territory = frappe.db.get_value("Territory", {}, "name")
        if not territory:
            territory_doc = frappe.get_doc(
                {
                    "doctype": "Territory",
                    "territory_name": "All Territories",
                    "is_group": 0,
                }
            )
            territory_doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            territory = territory_doc.name

        customer_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Easy Maid Stripe Smoke Customer",
                "customer_group": "Residential",
                "territory": territory,
                "customer_type": "Individual",
            }
        )
        customer_doc.insert(ignore_permissions=True)
        customer = customer_doc.name

    item_code = frappe.db.get_value("Item", {"item_code": "EMS-STD-CLEAN"}, "item_code") or frappe.db.get_value(
        "Item", {"disabled": 0, "is_stock_item": 0}, "item_code"
    )
    if not item_code:
        frappe.throw("No service Item available for invoice creation.")

    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": company,
            "currency": company_currency,
            "customer": customer,
            "posting_date": today(),
            "due_date": add_days(today(), 7),
            "set_posting_time": 1,
            "items": [
                {
                    "item_code": item_code,
                    "qty": 1,
                    "rate": 149,
                }
            ],
        }
    )
    invoice.insert(ignore_permissions=True)

    try:
        invoice.submit()
        created_submitted = True
    except frappe.ValidationError as exc:
        # Dev sites may be missing accounting defaults needed for GL posting.
        if "Round Off Account" not in str(exc):
            raise
        created_submitted = False

    frappe.db.commit()

    return {
        "sales_invoice": invoice.name,
        "created": True,
        "submitted": created_submitted,
        "customer": customer,
        "item_code": item_code,
    }


def _create_or_get_smoke_lead(customer_email: str) -> str:
    prefix = "SMOKE-QUOTE"
    existing = frappe.db.get_value("Lead", {"email_id": customer_email, "lead_name": ["like", f"{prefix}%"]}, "name")
    if existing:
        return existing

    lead = frappe.get_doc(
        {
            "doctype": "Lead",
            "lead_name": f"{prefix}-{frappe.generate_hash(length=6)}",
            "email_id": customer_email,
            "source": "Website",
            "status": "Lead",
            "city": "Jersey City",
            "state": "New Jersey",
            "notes": "Automated smoke lead",
        }
    )
    lead.insert(ignore_permissions=True)
    return lead.name
