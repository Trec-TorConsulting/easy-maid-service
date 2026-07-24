app_name = "easy_maid"
app_title = "Easy Maid"
app_publisher = "Easy Maid Service"
app_description = "Cleaning-company back-office and customer portal on Frappe/ERPNext."
app_email = "trecto28@gmail.com"
app_license = "MIT"

# ERPNext is required — this app layers on top of it.
required_apps = ["erpnext"]

# Run idempotent baseline setup after app installation on a site.
after_install = "easy_maid.easy_maid.setup.bootstrap.bootstrap_easymaid_defaults"

# ---------------------------------------------------------------------------
# Fixtures
# Export configured records (roles, tax templates, service Items, etc.) so the
# instance is reproducible:  bench --site <site> export-fixtures
# ---------------------------------------------------------------------------
fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Easy Maid Owner", "Easy Maid Client", "Easy Maid Cleaner"]]]},
	{"dt": "Customer Group", "filters": [["name", "in", ["Residential", "Commercial"]]]},
	{"dt": "Department", "filters": [["name", "in", ["Cleaning"]]]},
	{"dt": "Designation", "filters": [["name", "in", ["Cleaner", "Lead Cleaner"]]]},
	{"dt": "Sales Taxes and Charges Template", "filters": [["title", "in", ["NJ Sales Tax"]]]},
	{"dt": "Item", "filters": [["item_code", "like", "EMS-%"]]},
	{"dt": "Item Price", "filters": [["item_code", "like", "EMS-%"]]},
	{"dt": "Web Form", "filters": [["name", "in", ["Request a Quote"]]]},
	{"dt": "Print Format", "filters": [["name", "in", ["Easy Maid Quotation", "Easy Maid Receipt"]]]},
	{"dt": "Letter Head", "filters": [["name", "in", ["Easy Maid Letterhead"]]]},
	{"dt": "Shift Type", "filters": [["name", "in", ["Easy Maid Morning", "Easy Maid Afternoon"]]]},
	{"dt": "Custom Field", "filters": [["name", "in", [
		"Employee-easymaid_service_area",
		"Employee-easymaid_skills",
		"Employee-easymaid_certifications"
	]]]}
]

# ---------------------------------------------------------------------------
# Scheduled tasks
# The recurring-visit generator MUST be idempotent (unique per Booking + date).
# Implement in easy_maid/easy_maid/tasks.py -> generate_recurring_visits().
# ---------------------------------------------------------------------------
scheduler_events = {
	"daily": [
		"easy_maid.easy_maid.tasks.generate_recurring_visits",
	],
}

# ---------------------------------------------------------------------------
# Permission scoping
# Clients see only their own records; cleaners see only assigned visits.
# Implement query conditions + has_permission hooks per capability specs.
# ---------------------------------------------------------------------------
permission_query_conditions = {
	"Service Visit": "easy_maid.easy_maid.permissions.service_visit_query",
	"Booking": "easy_maid.easy_maid.permissions.booking_query",
	"Employee": "easy_maid.easy_maid.permissions.employee_query",
	"Salary Slip": "easy_maid.easy_maid.permissions.salary_slip_query",
}
has_permission = {
	"Service Visit": "easy_maid.easy_maid.permissions.service_visit_has_permission",
	"Employee": "easy_maid.easy_maid.permissions.employee_has_permission",
	"Salary Slip": "easy_maid.easy_maid.permissions.salary_slip_has_permission",
}

# ---------------------------------------------------------------------------
# Document events (e.g., enforce the 24-hour cancel/reschedule policy)
# ---------------------------------------------------------------------------
doc_events = {
	"Service Visit": {
		"before_cancel": "easy_maid.easy_maid.booking_policy.enforce_24h_notice",
		"validate": "easy_maid.easy_maid.booking_policy.validate_reschedule_window",
	},
}

# ---------------------------------------------------------------------------
# Website / frontend (Frappe UI Vue app is served from www/ or a bundled route)
# ---------------------------------------------------------------------------
app_include_css = ["/assets/easy_maid/frontend/main.css"]
app_include_js = ["/assets/easy_maid/frontend/main.js"]

# website_route_rules = [
#     {"from_route": "/app-portal/<path:app_path>", "to_route": "app-portal"},
# ]
