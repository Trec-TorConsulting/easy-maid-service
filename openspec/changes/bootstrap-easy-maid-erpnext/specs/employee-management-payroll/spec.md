## ADDED Requirements

### Requirement: Cleaner records
The system SHALL manage cleaners as ERPNext Employees with the fields needed to staff cleaning jobs.

#### Scenario: Onboard a cleaner
- **WHEN** an Owner/Admin creates an Employee record for a cleaner
- **THEN** the record stores identity, contact, employment status, and cleaning-relevant attributes (e.g., skills/certifications and service area)

#### Scenario: Deactivate a cleaner
- **WHEN** a cleaner leaves
- **THEN** their Employee record can be marked inactive/left so they no longer appear for new assignments

### Requirement: Shifts and availability
The system SHALL support defining shifts/availability so dispatch reflects who can work when.

#### Scenario: Assign a shift
- **WHEN** an Owner/Admin assigns a shift to a cleaner
- **THEN** the shift is recorded and visible when assigning that cleaner to visits

### Requirement: Payroll
The system SHALL run payroll for cleaners using native ERPNext HR/Payroll.

#### Scenario: Configure pay
- **WHEN** an Owner/Admin sets up a cleaner's salary structure
- **THEN** the structure (e.g., hourly/period pay and components) is stored and assigned to the Employee

#### Scenario: Process a payroll run
- **WHEN** an Owner/Admin processes payroll for a period
- **THEN** ERPNext generates Salary Slips for the included cleaners and posts the resulting accounting entries

### Requirement: Payroll access control
The system SHALL restrict payroll data to authorized roles.

#### Scenario: Cleaners cannot see others' pay
- **WHEN** an Employee/Cleaner is logged in
- **THEN** they cannot view other employees' salary or payroll data
