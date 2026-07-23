## ADDED Requirements

### Requirement: Invoicing
The system SHALL generate ERPNext Sales Invoices for completed cleanings, both one-time and recurring.

#### Scenario: Invoice a completed one-time visit
- **WHEN** a one-time Service Visit is marked Completed
- **THEN** staff can generate a Sales Invoice for that visit's service(s) and amount

#### Scenario: Recurring invoices are automatic
- **WHEN** a recurring Booking's billing schedule is due
- **THEN** ERPNext generates the Sales Invoice automatically via Subscription/recurring Sales Order

### Requirement: Online payments
The system SHALL allow clients to pay invoices online through the **Stripe** payment gateway using hosted checkout, and SHALL record the payment against the invoice.

#### Scenario: Client pays an invoice
- **WHEN** a client opens an unpaid invoice in the portal and pays via Stripe hosted checkout
- **THEN** the payment is captured and a Payment Entry is recorded that reconciles the invoice to Paid

#### Scenario: No card data on our servers
- **WHEN** a client enters card details
- **THEN** the card data is handled by Stripe hosted checkout and never stored on the application servers

#### Scenario: Payment failure is handled
- **WHEN** a Stripe payment fails or is declined
- **THEN** the invoice remains unpaid and the client is shown a clear failure message with the option to retry

### Requirement: Bookkeeping
The system SHALL maintain accurate double-entry bookkeeping so owners can see the financial state of the business.

#### Scenario: Ledger entries are posted
- **WHEN** an invoice is submitted and a payment is recorded
- **THEN** the corresponding General Ledger entries are posted to the correct income, receivable, and cash/bank accounts

#### Scenario: Financial reports are available
- **WHEN** an Owner/Admin opens financial reports
- **THEN** they can view standard reports such as Accounts Receivable, Profit and Loss, and General Ledger for the company

### Requirement: Receipts
The system SHALL provide clients a branded receipt/invoice document.

#### Scenario: Download receipt
- **WHEN** a client's invoice is paid
- **THEN** the client can download a branded PDF invoice/receipt
