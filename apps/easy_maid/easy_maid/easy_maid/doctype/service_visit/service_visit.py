from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from easy_maid.easy_maid.permissions_logic import can_transition_visit_status


class ServiceVisit(Document):
    def validate(self):
        self._validate_window()
        self._validate_unique_booking_start()
        self._validate_crew_overlap()
        self._validate_assignment_for_status_change()
        self._sync_completion_timestamp()

    def _validate_window(self):
        if self.scheduled_end and self.scheduled_start and self.scheduled_end <= self.scheduled_start:
            frappe.throw("scheduled_end must be after scheduled_start")

    def _validate_unique_booking_start(self):
        if not self.booking or not self.scheduled_start:
            return
        duplicate = frappe.db.exists(
            "Service Visit",
            {
                "name": ["!=", self.name],
                "booking": self.booking,
                "scheduled_start": self.scheduled_start,
                "docstatus": ["<", 2],
            },
        )
        if duplicate:
            frappe.throw("A Service Visit already exists for this booking at the same scheduled start time")

    def _validate_crew_overlap(self):
        if not self.crew:
            return

        for row in self.crew:
            if not row.employee:
                continue
            overlaps = frappe.db.sql(
                """
                select sv.name
                from `tabService Visit` sv
                inner join `tabCrew Assignment` ca on ca.parent = sv.name
                where sv.name != %(name)s
                  and sv.docstatus < 2
                  and ca.employee = %(employee)s
                  and sv.scheduled_start < %(scheduled_end)s
                  and sv.scheduled_end > %(scheduled_start)s
                limit 1
                """,
                {
                    "name": self.name or "",
                    "employee": row.employee,
                    "scheduled_start": self.scheduled_start,
                    "scheduled_end": self.scheduled_end,
                },
                as_dict=True,
            )
            if overlaps:
                frappe.throw(
                    f"Employee {row.employee} is already assigned to overlapping visit {overlaps[0]['name']}"
                )

    def _validate_assignment_for_status_change(self):
        if self.is_new() or self.status not in {"In Progress", "Completed"}:
            return

        old_status = frappe.db.get_value("Service Visit", self.name, "status")
        roles = set(frappe.get_roles(frappe.session.user))

        employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        assigned = False
        if employee:
            assigned = any((row.employee == employee) for row in self.crew)
            if not assigned:
                assigned = bool(
                    frappe.db.exists(
                        "Crew Assignment",
                        {
                            "parent": self.name,
                            "parenttype": "Service Visit",
                            "employee": employee,
                        },
                    )
                )

        if not can_transition_visit_status(
            old_status=old_status,
            new_status=self.status,
            roles=roles,
            is_assigned_cleaner=assigned,
        ):
            frappe.throw("Only assigned cleaners can mark this visit In Progress or Completed")

    def _sync_completion_timestamp(self):
        if self.status == "Completed" and not self.completed_on:
            self.completed_on = now_datetime()
        if self.status != "Completed":
            self.completed_on = None
