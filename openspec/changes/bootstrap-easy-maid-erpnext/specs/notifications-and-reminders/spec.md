## ADDED Requirements

### Requirement: Booking and visit confirmations
The system SHALL send confirmation notifications when a Booking is created and when Service Visits are scheduled, so clients and assigned cleaners know what to expect.

#### Scenario: Client booking confirmation
- **WHEN** a Booking is confirmed for a client
- **THEN** the client receives a branded confirmation (email, and SMS when a mobile number and SMS are configured) with the service, address, date/time, and price

#### Scenario: Cleaner assignment notification
- **WHEN** a cleaner is assigned to a Service Visit
- **THEN** that cleaner is notified of the visit with time, address, and service details

### Requirement: Visit reminders
The system SHALL send reminders ahead of a scheduled Service Visit to reduce no-shows.

#### Scenario: Client reminder before a visit
- **WHEN** a Service Visit is approximately 24 hours away
- **THEN** the client receives a reminder that also states the 24-hour cancellation/reschedule policy

#### Scenario: Cleaner day-of reminder
- **WHEN** a cleaner has assigned visits for the day
- **THEN** the cleaner receives a reminder of their scheduled jobs

### Requirement: Billing and payment notifications
The system SHALL notify clients about invoices and payment outcomes.

#### Scenario: Invoice issued
- **WHEN** a Sales Invoice is issued to a client
- **THEN** the client receives a branded email with the invoice and a link to pay online

#### Scenario: Payment receipt
- **WHEN** a client's payment is recorded as Paid
- **THEN** the client receives a branded receipt confirmation

### Requirement: Lead and quote acknowledgements
The system SHALL acknowledge public quote requests and quotation delivery.

#### Scenario: Quote request acknowledgement
- **WHEN** a visitor submits the public Request a Quote form
- **THEN** they receive an acknowledgement email confirming the request was received

#### Scenario: Quotation delivery
- **WHEN** staff send a Quotation to a prospect
- **THEN** the prospect receives the branded Quotation PDF by email

### Requirement: Configurable, branded templates
The system SHALL implement notifications using native ERPNext Notification / Email Template / Print Format mechanisms so message content, timing, and enablement are configurable by an admin without a code deploy, and all templates carry Maidurday branding.

#### Scenario: Edit a template without deploying code
- **WHEN** an admin edits a notification's subject or body
- **THEN** subsequent notifications use the updated content without any code change or redeploy

#### Scenario: Enable or disable a notification
- **WHEN** an admin disables a specific notification
- **THEN** that notification stops being sent while others continue

### Requirement: Channel configuration and consent
The system SHALL configure email and (optionally) SMS channels with credentials stored only in Kubernetes Secrets / site config, and SHALL respect client contact preferences and consent.

#### Scenario: Secrets are not in the repo
- **WHEN** SMS/email provider credentials are configured
- **THEN** they are sourced from Secrets / site config and never committed to the repository

#### Scenario: Opt-out is honored
- **WHEN** a client has opted out of a notification channel
- **THEN** the system does not send them messages on that channel, and marketing emails include an unsubscribe mechanism

### Requirement: Reliable, non-duplicated delivery
The system SHALL send notifications asynchronously via background workers and SHALL avoid duplicate sends for the same event.

#### Scenario: Sends do not block the request
- **WHEN** an event triggers a notification
- **THEN** the message is enqueued and sent by a background worker without blocking the originating user action

#### Scenario: No duplicate notification
- **WHEN** the same triggering event is processed more than once (e.g., retry)
- **THEN** the client receives at most one notification for that event

#### Scenario: Failures are logged
- **WHEN** a notification fails to send
- **THEN** the failure is logged for follow-up and does not crash the originating operation
