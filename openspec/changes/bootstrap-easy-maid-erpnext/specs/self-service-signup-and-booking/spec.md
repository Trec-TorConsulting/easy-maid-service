## ADDED Requirements

### Requirement: Self-service account signup
The system SHALL let a brand-new prospect create a client account online without any staff step, provisioning the underlying ERPNext Customer and a portal User granted only the client role.

#### Scenario: Visitor creates an account
- **WHEN** a visitor completes the online signup form with name, email, and password (or verified email link)
- **THEN** a portal User with the client role and a linked Customer record are created
- **AND** the new user can log in to the client portal immediately

#### Scenario: Email verification
- **WHEN** a visitor signs up
- **THEN** the system verifies the email (e.g., confirmation link) before the account can be used to book, to reduce abuse

#### Scenario: New user sees only their own data
- **WHEN** a newly signed-up client logs in
- **THEN** they can access only their own Customer, Bookings, visits, and invoices, and no back-office or other customers' data

### Requirement: Online booking for new customers
The system SHALL let a signed-up client book a cleaning end-to-end online — choosing service, address, and date or recurring cadence — without a staff member intervening, creating a Booking (and its Service Visit(s)).

#### Scenario: Complete an online booking
- **WHEN** a signed-up client selects a service, enters a service address, and chooses a one-time date or a recurring cadence
- **THEN** a Booking is created with the selected service, address, price, and schedule, and the corresponding Service Visit(s) are generated

#### Scenario: Recurring cadence online
- **WHEN** a client chooses weekly, biweekly, or monthly cadence with a start date
- **THEN** the Booking stores the recurrence rule and upcoming visits are generated per the bookings capability

### Requirement: Transparent pricing before submit
The system SHALL show the client an itemized price estimate, including the configured New Jersey sales tax, before they confirm an online booking, and SHALL compute the authoritative total server-side.

#### Scenario: Estimate shown before confirmation
- **WHEN** a client has selected services and options
- **THEN** an itemized estimate with subtotal, NJ tax, and total is displayed before they confirm

#### Scenario: Server computes the authoritative price
- **WHEN** a booking is submitted
- **THEN** the server recomputes the price from the ERPNext Price List and tax template and does not trust any client-supplied total

### Requirement: Pay online at booking
The system SHALL allow a client to pay or prepay for an online booking via the Stripe hosted checkout, reconciling the resulting invoice, without card data touching the application servers.

#### Scenario: Prepay a booking
- **WHEN** a client chooses to pay at booking time
- **THEN** they are taken to Stripe hosted checkout, and on success a Payment Entry is recorded reconciling the related invoice to Paid

#### Scenario: Book now, pay later
- **WHEN** online prepayment is not required for the selected service
- **THEN** the booking is confirmed and the client can pay the resulting invoice later from the portal

### Requirement: Guardrails and abuse prevention
The system SHALL protect the public signup and booking endpoints against abuse and invalid input.

#### Scenario: Throttling and anti-spam
- **WHEN** signup or booking requests exceed a reasonable rate from one source
- **THEN** the system throttles or blocks the excess requests and applies anti-spam protection (e.g., honeypot/captcha)

#### Scenario: Server-side validation
- **WHEN** a signup or booking payload is submitted
- **THEN** required fields, address, date, and service validity are validated server-side and invalid requests are rejected with a clear message

### Requirement: Graceful fallback to quote
The system SHALL fall back to the quote-request flow when a request cannot be fulfilled as a direct online booking.

#### Scenario: Out-of-area or custom job
- **WHEN** a client requests service outside the bookable area or a job that needs a custom estimate
- **THEN** the system routes them to Request a Quote instead of failing silently, capturing their details as a Lead
