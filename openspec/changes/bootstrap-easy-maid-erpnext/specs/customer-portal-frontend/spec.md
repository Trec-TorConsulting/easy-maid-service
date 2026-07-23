## ADDED Requirements

### Requirement: Single unified frontend
The system SHALL provide one Frappe UI (Vue) web application served from the `easy_maid` app that acts as the single place for owners, clients, and cleaners, presenting a role-appropriate experience after login.

#### Scenario: Role-based landing
- **WHEN** a user logs in
- **THEN** they land on the experience for their role (Owner/Admin, Client/Customer, or Employee/Cleaner) without seeing other roles' navigation

#### Scenario: Authentication
- **WHEN** an unauthenticated user opens a protected page
- **THEN** they are redirected to log in and returned to the requested page after authenticating

### Requirement: Owner/Admin experience
The system SHALL give owners a dashboard summarizing the business and access to bookings, dispatch, invoicing, and reports.

#### Scenario: Owner dashboard
- **WHEN** an Owner/Admin opens the app
- **THEN** they see key metrics (e.g., upcoming visits, unassigned jobs, revenue/AR summary) and can navigate to dispatch, bookings, and financial reports

### Requirement: Client experience
The system SHALL let clients self-serve their cleaning relationship.

#### Scenario: Client books a cleaning
- **WHEN** a logged-in client requests a cleaning (one-time or recurring)
- **THEN** they can select a service, address, and date/cadence and submit a Booking request

#### Scenario: Client manages account
- **WHEN** a client opens their account
- **THEN** they can view upcoming/past visits, reschedule or cancel a visit subject to the 24-hour notice policy, and view and pay invoices

#### Scenario: Reschedule blocked inside policy window
- **WHEN** a client tries to reschedule or cancel a visit less than 24 hours before its start
- **THEN** the portal prevents the action and explains the 24-hour minimum notice policy

### Requirement: Cleaner experience
The system SHALL give cleaners a focused view of their work.

#### Scenario: Cleaner sees today's jobs
- **WHEN** a cleaner opens the app
- **THEN** they see their assigned visits with time, address, service details, and can mark a visit In Progress and Completed

### Requirement: Responsive and accessible UI
The system SHALL present a responsive interface usable on phones and desktops.

#### Scenario: Mobile usability
- **WHEN** a cleaner uses the app on a phone
- **THEN** the schedule and job actions are usable without horizontal scrolling

### Requirement: Consistent branding
The system SHALL present "Easy Maid Service" branding consistently across the frontend.

#### Scenario: Branded UI
- **WHEN** any user views the app
- **THEN** the "Easy Maid Service" name, logo placeholder, and theme are shown
