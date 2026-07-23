## ADDED Requirements

### Requirement: Web-to-lead capture
The system SHALL capture prospective customers from a public web form into ERPNext Leads without requiring the prospect to log in.

#### Scenario: Public form creates a lead
- **WHEN** a visitor submits the "Request a Quote" web form with name, contact, address, and requested service
- **THEN** a new ERPNext Lead is created with those details and a source of "Website"
- **AND** the visitor sees a confirmation message

#### Scenario: Spam protection
- **WHEN** the web form is submitted
- **THEN** basic anti-spam protection (e.g., captcha/honeypot or rate limiting) is enforced before a Lead is created

### Requirement: Lead qualification
The system SHALL let staff qualify a Lead and convert it into an Opportunity.

#### Scenario: Convert lead to opportunity
- **WHEN** an Owner/Admin qualifies a Lead
- **THEN** they can convert it to an Opportunity linked to the originating Lead

### Requirement: Quoting
The system SHALL let staff produce a Quotation for cleaning services from an Opportunity or Lead using the service catalog.

#### Scenario: Create quotation
- **WHEN** staff build a Quotation for a customer
- **THEN** they can add service Items with quantities and rates and the totals (including tax) are calculated automatically

#### Scenario: Send quotation
- **WHEN** a Quotation is finalized
- **THEN** it can be emailed to the prospect as a branded PDF

### Requirement: Quotation acceptance
The system SHALL support converting an accepted Quotation into a Sales Order that seeds a booking.

#### Scenario: Accept quotation
- **WHEN** a customer accepts a Quotation
- **THEN** staff can convert it to a Sales Order
- **AND** the Sales Order can be used to create a Booking (see bookings capability)
