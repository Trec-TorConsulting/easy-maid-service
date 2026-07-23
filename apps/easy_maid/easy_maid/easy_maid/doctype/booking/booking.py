from __future__ import annotations

import frappe
from frappe.model.document import Document


class Booking(Document):
    def validate(self):
        self._validate_type_requirements()
        self._validate_recurrence_fields()

    def _validate_type_requirements(self):
        if self.booking_type == "One-time" and not self.scheduled_date:
            frappe.throw("scheduled_date is required for one-time bookings")

        if self.booking_type == "Recurring" and not self.start_date:
            frappe.throw("start_date is required for recurring bookings")

    def _validate_recurrence_fields(self):
        if self.booking_type != "Recurring":
            return

        if self.frequency not in {"Weekly", "Biweekly", "Monthly"}:
            frappe.throw("frequency must be Weekly, Biweekly, or Monthly for recurring bookings")

        if self.interval is None or self.interval < 1:
            frappe.throw("interval must be >= 1")

        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw("end_date cannot be before start_date")

        if self.occurrences and self.occurrences < 1:
            frappe.throw("occurrences must be >= 1")
