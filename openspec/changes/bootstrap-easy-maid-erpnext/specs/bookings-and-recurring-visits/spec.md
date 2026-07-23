## ADDED Requirements

### Requirement: Booking record
The system SHALL provide a custom `Booking` DocType that represents an agreement to clean a specific service location, either once or on a recurring cadence. A Booking MUST link to a Customer and a service address and reference the service Item(s).

#### Scenario: Create a one-time booking
- **WHEN** staff or a client creates a Booking for a specific date and service
- **THEN** the Booking is saved with the customer, service address, chosen service Item(s), price, and a single scheduled date

#### Scenario: Booking seeded from a Sales Order
- **WHEN** a Sales Order created from an accepted Quotation is confirmed
- **THEN** a Booking can be generated from it, carrying over the customer, services, and pricing

### Requirement: Recurring cadence
The system SHALL support recurring Bookings on weekly, biweekly, and monthly cadences with a start date and an optional end date or occurrence count.

#### Scenario: Configure recurrence
- **WHEN** a Booking is marked recurring with a cadence and start date
- **THEN** the Booking stores the recurrence rule (frequency, interval, start, and optional end/occurrences)

#### Scenario: Generate upcoming visits
- **WHEN** a recurring Booking is active
- **THEN** the system generates individual `Service Visit` records for upcoming occurrences up to a configurable horizon
- **AND** it does not create duplicate visits for a date already generated

### Requirement: Service Visit record
The system SHALL provide a custom `Service Visit` DocType representing a single scheduled cleaning occurrence with its own date/time window, status, and link back to its Booking.

#### Scenario: Visit lifecycle
- **WHEN** a Service Visit is created
- **THEN** it has a status of at least Scheduled, In Progress, Completed, or Cancelled and a scheduled date/time window

#### Scenario: Cancel a single visit
- **WHEN** a client or staff cancels one occurrence of a recurring Booking
- **THEN** only that Service Visit is cancelled and future visits remain scheduled

### Requirement: Cancellation / reschedule notice policy
The system SHALL require at least **24 hours notice** for a client to cancel or reschedule a Service Visit. The policy MUST be enforced server-side, not only in the UI. Owners/Admins MAY override inside the window.

#### Scenario: Client cancels with sufficient notice
- **WHEN** a client cancels or reschedules a Service Visit more than 24 hours before its scheduled start
- **THEN** the change is accepted

#### Scenario: Client blocked inside the 24-hour window
- **WHEN** a client attempts to cancel or reschedule a Service Visit less than 24 hours before its scheduled start
- **THEN** the action is rejected server-side with a message explaining the 24-hour policy

#### Scenario: Admin override
- **WHEN** an Owner/Admin cancels or reschedules a visit inside the 24-hour window
- **THEN** the change is permitted and recorded

### Requirement: Recurring billing linkage
The system SHALL tie recurring Bookings to native ERPNext billing so recurring revenue is invoiced automatically.

#### Scenario: Recurring invoices are generated
- **WHEN** a recurring Booking is linked to a Subscription (or recurring Sales Order)
- **THEN** ERPNext generates the recurring Sales Invoices on the configured schedule without manual re-entry
