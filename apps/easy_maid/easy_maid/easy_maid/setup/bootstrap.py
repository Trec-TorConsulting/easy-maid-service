from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate, today

COMPANY = "Easy Maid Service"
ABBR = "EMS"
CURRENCY = "USD"
COUNTRY = "United States"
STATE = "New Jersey"

SERVICE_ITEMS = [
    ("EMS-STD-CLEAN", "Standard Clean", 150),
    ("EMS-DEEP-CLEAN", "Deep Clean", 275),
    ("EMS-MOVE-IN-OUT", "Move-In/Out Clean", 350),
    ("EMS-RECUR-CLEAN", "Recurring Clean", 130),
    ("EMS-ADDON-INSIDE-FRIDGE", "Add-on: Inside Fridge", 35),
]


def _ensure_doc(doctype: str, name: str, values: dict):
    if frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        doc.save(ignore_permissions=True)
        return doc

    values = {**values, "doctype": doctype, "name": name}
    doc = frappe.get_doc(values)
    doc.insert(ignore_permissions=True)
    return doc


def _ensure_role(role_name: str):
    if frappe.db.exists("Role", role_name):
        return
    frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def _ensure_warehouse_types():
    if not frappe.db.exists("DocType", "Warehouse Type"):
        return

    if frappe.db.exists("Warehouse Type", "Transit"):
        return

    frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(
        ignore_permissions=True
    )


def _ensure_company():
    if frappe.db.exists("Company", COMPANY):
        return frappe.get_doc("Company", COMPANY)

    company = frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": COMPANY,
            "abbr": ABBR,
            "default_currency": CURRENCY,
            "country": COUNTRY,
            "default_holiday_list": "",
        }
    )
    company.insert(ignore_permissions=True)
    return company


def _ensure_customer_groups():
    for group in ["Residential", "Commercial"]:
        if not frappe.db.exists("Customer Group", group):
            frappe.get_doc(
                {
                    "doctype": "Customer Group",
                    "customer_group_name": group,
                    "is_group": 0,
                }
            ).insert(ignore_permissions=True)


def _ensure_fiscal_year(company_name: str):
    current = getdate(today())
    fiscal_label = f"FY-{current.year}"
    if not frappe.db.exists("Fiscal Year", fiscal_label):
        fiscal_year = frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": fiscal_label,
                "year_start_date": f"{current.year}-01-01",
                "year_end_date": f"{current.year}-12-31",
            }
        )
        fiscal_year.insert(ignore_permissions=True)

    company = frappe.get_doc("Company", company_name)
    company_meta = frappe.get_meta("Company")
    if company_meta.has_field("default_fiscal_year"):
        current_value = company.get("default_fiscal_year")
        if current_value != fiscal_label:
            company.db_set("default_fiscal_year", fiscal_label, update_modified=False)

    return fiscal_label


def _ensure_employee_structures(company_name: str):
    existing_department = frappe.db.get_value(
        "Department",
        {"department_name": "Cleaning"},
        "name",
    )
    if not existing_department:
        dept_payload = {"doctype": "Department", "department_name": "Cleaning"}
        dept_meta = frappe.get_meta("Department")
        if dept_meta.has_field("company"):
            dept_payload["company"] = company_name
        frappe.get_doc(dept_payload).insert(ignore_permissions=True, ignore_if_duplicate=True)

    for designation in ["Cleaner", "Lead Cleaner"]:
        if not frappe.db.exists("Designation", designation):
            frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(
                ignore_permissions=True
            )


def _ensure_custom_field(payload: dict):
    existing = frappe.db.get_value(
        "Custom Field",
        {"dt": payload["dt"], "fieldname": payload["fieldname"]},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Custom Field", existing)
        doc.update(payload)
        doc.save(ignore_permissions=True)
        return existing

    custom = frappe.get_doc({"doctype": "Custom Field", **payload})
    custom.insert(ignore_permissions=True)
    return custom.name


def _ensure_employee_custom_fields():
    if not frappe.db.exists("DocType", "Custom Field"):
        return []

    created = []
    for payload in [
        {
            "dt": "Employee",
            "fieldname": "easymaid_service_area",
            "label": "Service Area",
            "fieldtype": "Data",
            "insert_after": "designation",
            "translatable": 0,
        },
        {
            "dt": "Employee",
            "fieldname": "easymaid_skills",
            "label": "Cleaning Skills",
            "fieldtype": "Small Text",
            "insert_after": "easymaid_service_area",
            "translatable": 0,
        },
        {
            "dt": "Employee",
            "fieldname": "easymaid_certifications",
            "label": "Certifications",
            "fieldtype": "Small Text",
            "insert_after": "easymaid_skills",
            "translatable": 0,
        },
    ]:
        created.append(_ensure_custom_field(payload))
    return created


def _ensure_shift_types():
    if not frappe.db.exists("DocType", "Shift Type"):
        return []

    ensured = []
    for shift_name, start_time, end_time in [
        ("Easy Maid Morning", "08:00:00", "12:00:00"),
        ("Easy Maid Afternoon", "12:30:00", "17:30:00"),
    ]:
        if frappe.db.exists("Shift Type", shift_name):
            shift = frappe.get_doc("Shift Type", shift_name)
        else:
            shift = frappe.get_doc({"doctype": "Shift Type", "shift_name": shift_name})

        shift.start_time = start_time
        shift.end_time = end_time
        shift.enable_auto_attendance = 0
        if shift.is_new():
            shift.insert(ignore_permissions=True)
        else:
            shift.save(ignore_permissions=True)
        ensured.append(shift.name)
    return ensured


def _ensure_item_group():
    root_item_group = "All Item Groups"
    if not frappe.db.exists("Item Group", root_item_group):
        # ERPNext setups can vary in root naming; use the first group in the tree.
        root_group_row = frappe.get_all(
            "Item Group",
            filters={"is_group": 1},
            fields=["name"],
            order_by="lft asc",
            limit=1,
        )
        root_item_group = root_group_row[0].name if root_group_row else None

    if not root_item_group:
        root_group = frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": "All Item Groups",
                "is_group": 1,
                "parent_item_group": "",
            }
        )
        root_group.insert(ignore_permissions=True, ignore_if_duplicate=True)
        root_item_group = root_group.name

    if not root_item_group:
        return None

    existing_group = frappe.db.get_value(
        "Item Group",
        {"item_group_name": "Cleaning Services"},
        "name",
    )
    if existing_group:
        return existing_group

    group = frappe.get_doc(
        {
            "doctype": "Item Group",
            "item_group_name": "Cleaning Services",
            "is_group": 0,
            "parent_item_group": root_item_group,
        }
    )
    group.insert(ignore_permissions=True, ignore_if_duplicate=True)
    return group.name


def _ensure_uom():
    if frappe.db.exists("UOM", "Nos"):
        return "Nos"

    uom = frappe.get_doc({"doctype": "UOM", "uom_name": "Nos", "enabled": 1})
    uom.insert(ignore_permissions=True, ignore_if_duplicate=True)
    return "Nos"


def _ensure_service_items(company_name: str):
    item_group_name = _ensure_item_group()
    if not item_group_name:
        return

    uom_name = _ensure_uom()

    if not frappe.db.exists("Price List", "Standard Selling"):
        frappe.get_doc(
            {
                "doctype": "Price List",
                "price_list_name": "Standard Selling",
                "enabled": 1,
                "buying": 0,
                "selling": 1,
                "currency": CURRENCY,
            }
        ).insert(ignore_permissions=True)

    for item_code, item_name, rate in SERVICE_ITEMS:
        if not frappe.db.exists("Item", item_code):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": item_code,
                    "item_name": item_name,
                    "item_group": item_group_name,
                    "stock_uom": uom_name,
                    "is_stock_item": 0,
                    "disabled": 0,
                }
            ).insert(ignore_permissions=True)

        existing = frappe.db.exists(
            "Item Price",
            {
                "item_code": item_code,
                "price_list": "Standard Selling",
                "currency": CURRENCY,
            },
        )
        if not existing:
            frappe.get_doc(
                {
                    "doctype": "Item Price",
                    "item_code": item_code,
                    "price_list": "Standard Selling",
                    "currency": CURRENCY,
                    "price_list_rate": rate,
                }
            ).insert(ignore_permissions=True)


def _ensure_nj_tax_template(company_name: str):
    template_name = "NJ Sales Tax"
    existing_template = frappe.db.get_value(
        "Sales Taxes and Charges Template",
        {"title": template_name, "company": company_name},
        "name",
    )
    if existing_template:
        return

    income_account = frappe.db.get_value(
        "Account",
        {
            "company": company_name,
            "account_name": ["like", "%Sales%"],
            "is_group": 0,
        },
        "name",
    )

    if not income_account:
        frappe.throw(_("No suitable Sales account found for NJ tax template setup"))

    template = frappe.get_doc(
        {
            "doctype": "Sales Taxes and Charges Template",
            "title": template_name,
            "company": company_name,
            "taxes": [
                {
                    "doctype": "Sales Taxes and Charges",
                    "charge_type": "On Net Total",
                    "account_head": income_account,
                    "description": "NJ Sales Tax",
                    "rate": 6.625,
                }
            ],
        }
    )
    template.insert(ignore_permissions=True, ignore_if_duplicate=True)


def _ensure_roles():
    for role in ["Easy Maid Owner", "Easy Maid Client", "Easy Maid Cleaner"]:
        _ensure_role(role)


def _ensure_branding(company_name: str):
    company = frappe.get_doc("Company", company_name)
    company.update(
        {
            "country": COUNTRY,
            "default_currency": CURRENCY,
            "state": STATE,
        }
    )
    company.save(ignore_permissions=True)

    website_settings = frappe.get_single("Website Settings")
    website_settings.update(
        {
            "app_name": COMPANY,
            "app_logo": "/assets/easy_maid/brand/logo-mark.svg",
        }
    )
    website_settings.save(ignore_permissions=True)


def _ensure_letter_head(company_name: str):
    if not frappe.db.exists("DocType", "Letter Head"):
        return False

    name = "Easy Maid Letterhead"
    content = """
<div style='font-family:Arial,sans-serif;'>
  <div style='display:flex;align-items:center;gap:10px;'>
    <img src='/assets/easy_maid/brand/logo-mark.svg' alt='Easy Maid' style='height:34px;' />
    <div>
      <strong>Easy Maid Service</strong><br />
      New Jersey, USA
    </div>
  </div>
</div>
""".strip()

    if frappe.db.exists("Letter Head", name):
        head = frappe.get_doc("Letter Head", name)
    else:
        head = frappe.get_doc({"doctype": "Letter Head", "letter_head_name": name, "company": company_name})

    head.content = content
    head.footer = "Thank you for choosing Easy Maid Service"
    head.is_default = 1
    if head.is_new():
        head.insert(ignore_permissions=True)
    else:
        head.save(ignore_permissions=True)
    return True


def _ensure_stripe_settings():
    """Best-effort Stripe settings bootstrap from site config.

    Expected site_config keys:
    - stripe_publishable_key
    - stripe_secret_key
    - stripe_webhook_secret
    """
    if not frappe.db.exists("DocType", "Stripe Settings"):
        return False

    publishable = frappe.conf.get("stripe_publishable_key")
    secret = frappe.conf.get("stripe_secret_key")
    webhook = frappe.conf.get("stripe_webhook_secret")
    if not publishable or not secret:
        return False

    stripe = frappe.get_single("Stripe Settings")
    updates = {
        "publishable_key": publishable,
        "secret_key": secret,
        "enabled": 1,
    }
    if webhook and hasattr(stripe, "webhook_secret"):
        updates["webhook_secret"] = webhook
    stripe.update(updates)
    stripe.save(ignore_permissions=True)
    return True


def _ensure_request_quote_web_form():
    """Best-effort native Web Form creation for Lead intake."""
    if not frappe.db.exists("DocType", "Web Form"):
        return False

    name = "Request a Quote"
    if frappe.db.exists("Web Form", name):
        return True

    try:
        web_form = frappe.get_doc(
            {
                "doctype": "Web Form",
                "title": name,
                "route": "request-a-quote",
                "module": "Easy Maid",
                "doc_type": "Lead",
                "login_required": 0,
                "is_standard": 1,
                "published": 1,
                "allow_edit": 0,
                "allow_multiple": 1,
                "web_form_fields": [
                    {"fieldname": "lead_name", "label": "Full Name", "fieldtype": "Data", "reqd": 1},
                    {"fieldname": "email_id", "label": "Email", "fieldtype": "Data", "reqd": 1},
                    {"fieldname": "mobile_no", "label": "Phone", "fieldtype": "Data", "reqd": 0},
                    {"fieldname": "city", "label": "City", "fieldtype": "Data", "reqd": 1},
                    {"fieldname": "state", "label": "State", "fieldtype": "Data", "reqd": 1},
                    {"fieldname": "notes", "label": "Service Details", "fieldtype": "Small Text", "reqd": 1},
                ],
            }
        )
        web_form.insert(ignore_permissions=True)
        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: Web Form bootstrap failed")
        return False


def _ensure_quotation_print_format():
    """Best-effort branded quotation print format seed."""
    if not frappe.db.exists("DocType", "Print Format"):
        return False

    name = "Easy Maid Quotation"
    if frappe.db.exists("Print Format", name):
        return True

    html = """
<div style='font-family:Arial,sans-serif;'>
  <h2 style='margin-bottom:0;'>Easy Maid Service</h2>
  <p style='margin-top:4px;'>Quotation: {{ doc.name }}</p>
  <p>Customer: {{ doc.party_name or doc.customer_name }}</p>
  <p>Total: {{ doc.get_formatted('grand_total') }}</p>
</div>
""".strip()

    try:
        pf = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "print_format_name": name,
                "doc_type": "Quotation",
                "module": "Easy Maid",
                "custom_format": 1,
                "disabled": 0,
                "raw_printing": 0,
                "html": html,
            }
        )
        pf.insert(ignore_permissions=True)
        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: Quotation print format bootstrap failed")
        return False


def _ensure_sales_invoice_print_format():
    if not frappe.db.exists("DocType", "Print Format"):
        return False

    name = "Easy Maid Receipt"
    if frappe.db.exists("Print Format", name):
        return True

    html = """
<div style='font-family:Arial,sans-serif;'>
  <h2 style='margin-bottom:0;'>Easy Maid Service</h2>
  <p style='margin-top:4px;'>Receipt: {{ doc.name }}</p>
  <p>Customer: {{ doc.customer_name or doc.customer }}</p>
  <p>Status: {{ doc.status }}</p>
  <p>Grand Total: {{ doc.get_formatted('grand_total') }}</p>
  <p>Outstanding: {{ doc.get_formatted('outstanding_amount') }}</p>
</div>
""".strip()

    try:
        pf = frappe.get_doc(
            {
                "doctype": "Print Format",
                "name": name,
                "print_format_name": name,
                "doc_type": "Sales Invoice",
                "module": "Easy Maid",
                "custom_format": 1,
                "disabled": 0,
                "raw_printing": 0,
                "html": html,
            }
        )
        pf.insert(ignore_permissions=True)
        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: Sales Invoice print format bootstrap failed")
        return False


def _ensure_payroll_scaffold(company_name: str):
    """Best-effort payroll baseline for cleaner salary setup."""
    required_doctypes = ["Salary Component", "Salary Structure"]
    for doctype in required_doctypes:
        if not frappe.db.exists("DocType", doctype):
            return False

    try:
        if not frappe.db.exists("Salary Component", "Basic"):
            basic = frappe.get_doc(
                {
                    "doctype": "Salary Component",
                    "salary_component": "Basic",
                    "type": "Earning",
                    "depends_on_payment_days": 1,
                    "is_tax_applicable": 1,
                }
            )
            basic.insert(ignore_permissions=True)

        if not frappe.db.exists("Salary Component", "Cleaner Travel Stipend"):
            stipend = frappe.get_doc(
                {
                    "doctype": "Salary Component",
                    "salary_component": "Cleaner Travel Stipend",
                    "type": "Earning",
                    "depends_on_payment_days": 0,
                    "is_tax_applicable": 0,
                }
            )
            stipend.insert(ignore_permissions=True)

        if not frappe.db.exists("Salary Structure", "Easy Maid Cleaner Monthly"):
            structure = frappe.get_doc(
                {
                    "doctype": "Salary Structure",
                    "name": "Easy Maid Cleaner Monthly",
                    "company": company_name,
                    "currency": CURRENCY,
                    "is_active": "Yes",
                    "salary_slip_based_on_timesheet": 0,
                    "earnings": [
                        {
                            "salary_component": "Basic",
                            "amount": 2800,
                        },
                        {
                            "salary_component": "Cleaner Travel Stipend",
                            "amount": 150,
                        },
                    ],
                }
            )
            structure.insert(ignore_permissions=True)

        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Easy Maid: payroll scaffold bootstrap failed")
        return False


@frappe.whitelist()
def bootstrap_easymaid_defaults():
    """Idempotent baseline setup for Easy Maid Service ERPNext backend."""
    _ensure_roles()
    _ensure_warehouse_types()
    company = _ensure_company()
    fiscal_year = _ensure_fiscal_year(company.name)
    _ensure_customer_groups()
    _ensure_employee_structures(company.name)
    employee_custom_fields = _ensure_employee_custom_fields()
    shift_types = _ensure_shift_types()
    _ensure_service_items(company.name)
    _ensure_nj_tax_template(company.name)
    _ensure_branding(company.name)
    letter_head_configured = _ensure_letter_head(company.name)
    payroll_scaffold_configured = _ensure_payroll_scaffold(company.name)
    stripe_configured = _ensure_stripe_settings()
    quote_web_form_configured = _ensure_request_quote_web_form()
    quotation_print_format_configured = _ensure_quotation_print_format()
    sales_invoice_print_format_configured = _ensure_sales_invoice_print_format()

    frappe.db.commit()
    return {
        "company": company.name,
        "fiscal_year": fiscal_year,
        "currency": CURRENCY,
        "state": STATE,
        "payroll_scaffold_configured": payroll_scaffold_configured,
        "stripe_configured": stripe_configured,
        "quote_web_form_configured": quote_web_form_configured,
        "letter_head_configured": letter_head_configured,
        "quotation_print_format_configured": quotation_print_format_configured,
        "sales_invoice_print_format_configured": sales_invoice_print_format_configured,
        "employee_custom_fields": employee_custom_fields,
        "shift_types": shift_types,
        "service_items": [code for code, _, _ in SERVICE_ITEMS],
    }
