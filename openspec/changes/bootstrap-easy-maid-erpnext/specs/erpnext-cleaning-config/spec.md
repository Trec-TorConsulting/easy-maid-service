## ADDED Requirements

### Requirement: Company and fiscal setup
The system SHALL configure a single ERPNext Company "Maidurday Cleaning Service" (abbreviation `EMS`) based in **New Jersey, USA** with base currency **USD**, a fiscal year, and a chart of accounts suitable for a service business. The display/company name is "Maidurday Cleaning Service"; internal technical identifiers (app `easy_maid`, module "Easy Maid", abbreviation `EMS`) are intentionally unchanged.

#### Scenario: Company exists
- **WHEN** ERPNext setup completes
- **THEN** a Company named "Maidurday Cleaning Service" (abbreviation `EMS`) exists with country United States, currency USD, and an active fiscal year
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
The system SHALL apply "Maidurday Cleaning Service" branding (company name, logo, brand palette) consistently across the Desk, the portal, the public website, and transactional documents. User-facing surfaces MUST show the Maidurday brand; internal technical identifiers (app `easy_maid`, module "Easy Maid", roles "Easy Maid Owner/Client/Cleaner", item-code prefix `EMS-`, asset path `/assets/easy_maid/`) remain unchanged.

#### Scenario: Branding shows
- **WHEN** a user views the app, the public website, or a printed invoice/quotation
- **THEN** the "Maidurday Cleaning Service" name and logo appear and no stray "Easy Maid Service" display text is shown

### Requirement: Maidurday-only Desk navigation
The system SHALL present the ERPNext Desk (`/app`, `/desk`) as a Maidurday cleaning workspace only, hiding stock Frappe/ERPNext modules and workspaces that are not relevant to the cleaning business, for Owners/Admins and Employees who use the Desk. Hiding MUST be reversible and MUST NOT revoke underlying DocType permissions, and it MUST be re-applied after each `bench migrate` (which re-syncs stock workspaces).

#### Scenario: Only Maidurday workspaces are visible
- **WHEN** an Owner/Admin or Employee opens `/app`
- **THEN** they see only the Maidurday cleaning workspace(s) and navigation, and stock ERPNext workspaces (e.g., Buying, Manufacturing, Stock, Assets, Quality) are hidden

#### Scenario: Declutter survives migration
- **WHEN** `bench migrate` re-syncs the stock workspaces
- **THEN** the Maidurday-only navigation is automatically re-applied so stock workspaces do not reappear

#### Scenario: Hiding does not remove access
- **WHEN** a workspace is hidden from the Desk
- **THEN** users with the appropriate role can still open the underlying DocTypes directly, and no permission is silently removed
