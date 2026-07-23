app_name = "easy_maid"
app_title = "Easy Maid"
app_publisher = "Easy Maid Service"
app_description = "Cleaning-company back-office and customer portal on Frappe/ERPNext."
app_email = "trecto28@gmail.com"
app_license = "MIT"

# ERPNext is required — this app layers on top of it.
required_apps = ["erpnext"]

# ---------------------------------------------------------------------------
# Fixtures
# Export configured records (roles, tax templates, service Items, etc.) so the
# instance is reproducible:  bench --site <site> export-fixtures
# ---------------------------------------------------------------------------
# fixtures = [
#     {"dt": "Role", "filters": [["name", "in", ["Cleaner", "Client", "Owner"]]]},
#     {"dt": "Sales Taxes and Charges Template"},
#     {"dt": "Customer Group", "filters": [["name", "in", ["Residential", "Commercial"]]]},
# ]

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
}
has_permission = {
	"Service Visit": "easy_maid.easy_maid.permissions.service_visit_has_permission",
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
# website_route_rules = [
#     {"from_route": "/app-portal/<path:app_path>", "to_route": "app-portal"},
# ]
