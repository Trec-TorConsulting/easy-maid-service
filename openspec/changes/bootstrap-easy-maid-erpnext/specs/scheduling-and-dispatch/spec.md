## ADDED Requirements

### Requirement: Crew assignment
The system SHALL let Owners/Admins assign one or more Employees (cleaners) to a Service Visit. ERPNext has no native field-service dispatch, so this is provided by the custom `easy_maid` app.

#### Scenario: Assign cleaners to a visit
- **WHEN** an Owner/Admin opens an unassigned Service Visit and assigns cleaner(s)
- **THEN** the visit records the assigned Employee(s) and their role on the job
- **AND** each assigned cleaner can see the visit on their schedule

#### Scenario: Prevent double-booking
- **WHEN** a cleaner is assigned to a visit that overlaps another assigned visit's time window
- **THEN** the system warns about the scheduling conflict before saving

### Requirement: Dispatch board
The system SHALL provide a dispatch view showing unassigned and assigned visits for a chosen day/range so staff can balance the workload.

#### Scenario: View the day's jobs
- **WHEN** an Owner/Admin opens the dispatch board for a date
- **THEN** they see all Service Visits for that date grouped by status and assigned cleaner
- **AND** unassigned visits are clearly highlighted

### Requirement: Crew calendar
The system SHALL present a calendar of Service Visits filterable by cleaner and by status.

#### Scenario: Cleaner views their calendar
- **WHEN** an Employee/Cleaner opens their calendar
- **THEN** they see only the visits assigned to them with time, address, and service details

### Requirement: Job execution and completion
The system SHALL let an assigned cleaner start and complete a visit, capturing completion time and optional notes.

#### Scenario: Complete a job
- **WHEN** an assigned cleaner marks a visit In Progress and then Completed
- **THEN** the visit status and completion timestamp are recorded
- **AND** the completed visit becomes eligible for invoicing

#### Scenario: Unassigned or unauthorized user cannot complete
- **WHEN** a cleaner not assigned to a visit attempts to change its status
- **THEN** the action is denied by permissions
