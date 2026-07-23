## ADDED Requirements

### Requirement: Company and fiscal setup
The system SHALL configure a single ERPNext Company "Easy Maid Service" based in **New Jersey, USA** with base currency **USD**, a fiscal year, and a chart of accounts suitable for a service business.

#### Scenario: Company exists
- **WHEN** ERPNext setup completes
- **THEN** a Company named "Easy Maid Service" exists with country United States, currency USD, and an active fiscal year
- **AND** a chart of accounts is assigned with income accounts for cleaning services

### Requirement: Service catalog
The system SHALL define the cleaning offerings as non-stock service Items with selling prices in a Price List.

#### Scenario: Service items exist
- **WHEN** the catalog is configured
- **THEN** service Items exist for the core offerings (e.g., Standard Clean, Deep Clean, Move-In/Out, Recurring Clean, Add-ons) marked as non-stock/service
- **AND** each has a selling rate in the default Price List

### Requirement: Tax configuration
The system SHALL configure New Jersey sales tax handling using a configurable Sales Taxes and Charges Template so the rate can be updated without code changes.

#### Scenario: Tax template applied
- **WHEN** a quotation or invoice is created for a NJ customer
- **THEN** the configured NJ Sales Taxes and Charges Template is available and applied per the company's tax rules

#### Scenario: Rate is configurable
- **WHEN** the applicable NJ sales-tax rate changes
- **THEN** an admin can update the tax template rate without a code deploy

### Requirement: Customer and employee grouping
The system SHALL define Customer Groups and Employee/Department structures appropriate for a cleaning company.

#### Scenario: Groups exist
- **WHEN** setup completes
- **THEN** Customer Groups (e.g., Residential, Commercial) and a Cleaning department/designation for employees exist

### Requirement: Roles and permissions
The system SHALL define role-based access for Owners/Admins, Clients/Customers, and Employees/Cleaners, granting each only the access appropriate to its function.

#### Scenario: Owner access
- **WHEN** an Owner/Admin logs in
- **THEN** they can access accounting, reports, all bookings, dispatch, and HR/payroll

#### Scenario: Cleaner access is limited
- **WHEN** an Employee/Cleaner logs in
- **THEN** they can view only their assigned jobs and schedule
- **AND** they cannot access accounting, other customers' data, or payroll of others

#### Scenario: Client access is limited
- **WHEN** a Client/Customer logs in
- **THEN** they can view and manage only their own bookings, invoices, and payments
- **AND** they cannot access other customers' data or back-office functions

### Requirement: Branding
The system SHALL apply "Easy Maid Service" branding (company name, logo placeholder) across the desk, portal, and transactional documents.

#### Scenario: Branding shows
- **WHEN** a user views the app or a printed invoice/quotation
- **THEN** the "Easy Maid Service" name and logo placeholder appear
