# Custom DocTypes — build guide

Create these three DocTypes under module **"Easy Maid"**. Preferred: build them in the Frappe
Desk UI on the running site (Owner/Admin), then export to this app with:

```bash
bench --site easymaid.trector.com export-fixtures     # or export via the DocType's "Export" action
```

That writes `booking/booking.json`, etc., beside this file. Each DocType also gets a
`<name>.py` controller for server-side logic.

> Spec: `openspec/changes/bootstrap-easy-maid-erpnext/specs/bookings-and-recurring-visits/spec.md`
> and `.../scheduling-and-dispatch/spec.md`. Design: `design.md` (D5).

## 1. Booking  (`booking/`)
Represents a one-time or recurring cleaning agreement.

| Field | Type | Notes |
| --- | --- | --- |
| customer | Link → Customer | required |
| service_address | Link → Address | required |
| services | Table (child) | one or more service Items + qty/rate |
| booking_type | Select | `One-time` / `Recurring` |
| scheduled_date | Date | for one-time |
| frequency | Select | `Weekly` / `Biweekly` / `Monthly` (recurring) |
| interval | Int | default 1 |
| start_date | Date | recurring start |
| end_date | Date | optional |
| occurrences | Int | optional (alternative to end_date) |
| sales_order | Link → Sales Order | optional link |
| subscription | Link → Subscription | optional (recurring billing) |
| status | Select | `Active` / `Paused` / `Cancelled` |

**Acceptance:** can save a one-time and a recurring Booking; recurring stores a complete rule.

## 2. Service Visit  (`service_visit/`)
A single scheduled cleaning occurrence.

| Field | Type | Notes |
| --- | --- | --- |
| booking | Link → Booking | required |
| customer | Link → Customer | fetched from Booking |
| service_address | Link → Address | fetched from Booking |
| scheduled_start | Datetime | required |
| scheduled_end | Datetime | required |
| status | Select | `Scheduled` / `In Progress` / `Completed` / `Cancelled` |
| completed_on | Datetime | set when Completed |
| crew | Table → Crew Assignment | assigned cleaners |
| notes | Small Text | optional |

**Server logic:** enforce the **24-hour** cancel/reschedule policy (admin override); mark
Completed → eligible for invoicing. Unique per (booking, scheduled_start) to keep the recurring
generator idempotent.

**Acceptance:** lifecycle transitions work; 24h policy rejects late client changes; only the
assigned cleaner can complete.

## 3. Crew Assignment  (`crew_assignment/`)  — child table of Service Visit
| Field | Type | Notes |
| --- | --- | --- |
| employee | Link → Employee | required |
| role | Select | `Lead` / `Helper` |

**Server logic:** warn/deny on overlapping assignments (double-booking).

**Acceptance:** assigning cleaners populates the visit; overlap is flagged.
