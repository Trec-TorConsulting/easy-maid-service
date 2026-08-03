## ADDED Requirements

### Requirement: Public marketing website
The system SHALL serve a public, unauthenticated marketing website for "Maidurday Cleaning Service" from the same Frappe instance and host (`easymaid.trector.com` / `maidurday.com`), so prospects can learn about the company and convert without logging in. The website MUST NOT be a separate application or host; it is served by Frappe's website layer alongside the app.

#### Scenario: Home page loads for a visitor
- **WHEN** an unauthenticated visitor opens the site root (`/`)
- **THEN** a branded Maidurday home/landing page is returned with a hero, value propositions, and a primary call to action
- **AND** no login is required to view it

#### Scenario: Website does not touch the existing instance
- **WHEN** the public website is served
- **THEN** it is served only by the `easymaid` instance and never references or mutates the existing `frappe` namespace or site `client.trector.com`

### Requirement: Core marketing pages
The system SHALL provide the following public pages, each branded, responsive, and reachable from the global navigation: Home, Services, Pricing, About, Contact, Service Areas, and FAQ.

#### Scenario: Services page describes offerings
- **WHEN** a visitor opens the Services page
- **THEN** it describes the cleaning offerings (e.g., Standard Clean, Deep Clean, Move-In/Out, Recurring Clean, Add-ons) that correspond to the ERPNext service catalog

#### Scenario: Pricing page communicates packages
- **WHEN** a visitor opens the Pricing page
- **THEN** it presents the service packages and starting prices consistent with the ERPNext Price List, and links to Request a Quote / Book Online

#### Scenario: Contact page shows how to reach the business
- **WHEN** a visitor opens the Contact page
- **THEN** it shows the business phone, email, service hours, and service area, plus a contact/quote form

#### Scenario: Service Areas page lists coverage
- **WHEN** a visitor opens the Service Areas page
- **THEN** it lists the New Jersey towns/areas served

#### Scenario: FAQ page answers common questions
- **WHEN** a visitor opens the FAQ page
- **THEN** it answers common questions (booking, cancellation policy, payment, what's included)

### Requirement: Global navigation, footer, and branding
The system SHALL present consistent Maidurday branding, a global navigation header, and a footer across every public page.

#### Scenario: Consistent header and footer
- **WHEN** a visitor views any public page
- **THEN** the Maidurday logo, name, primary navigation, and a footer (contact info, legal links, social links) are shown consistently
- **AND** the theme uses the Maidurday brand palette

### Requirement: Primary calls to action route into the app
The system SHALL surface primary calls to action — "Request a Quote", "Book Online", and "Client Login" — that route visitors into the corresponding app flows.

#### Scenario: Request a Quote
- **WHEN** a visitor clicks "Request a Quote"
- **THEN** they reach the public Request a Quote form that creates a Lead (see leads-and-quoting capability)

#### Scenario: Book Online
- **WHEN** a visitor clicks "Book Online"
- **THEN** they reach the self-service signup/booking flow (see self-service-signup-and-booking capability)

#### Scenario: Client Login
- **WHEN** a visitor clicks "Client Login"
- **THEN** they reach the authenticated client portal, and after login land on their client experience

### Requirement: Curated testimonials section
The system SHALL display a curated testimonials/reviews section using content managed by staff. This is display-only curated content and SHALL NOT collect post-clean ratings from customers (that remains out of scope).

#### Scenario: Testimonials are shown
- **WHEN** a visitor views the home page or a testimonials section
- **THEN** staff-curated testimonials (name, quote, optional rating) are displayed

#### Scenario: No public rating submission
- **WHEN** a visitor views the website
- **THEN** there is no public form to submit a post-clean rating (testimonials are managed by staff only)

### Requirement: Blog with seeded draft content
The system SHALL provide a blog section for cleaning tips and company updates, seeded with 5 starter articles that are created as drafts/unpublished so staff can review and publish them.

#### Scenario: Five draft articles are seeded
- **WHEN** the site is set up
- **THEN** 5 blog articles exist in an unpublished/draft state and are NOT visible on the public blog until an editor publishes them

#### Scenario: Publishing a blog post
- **WHEN** an editor publishes a draft article
- **THEN** it appears on the public blog index and its own page with title, content, and publish date

### Requirement: Legal pages
The system SHALL provide public Privacy Policy and Terms of Service pages linked from the footer.

#### Scenario: Legal pages are reachable
- **WHEN** a visitor clicks the Privacy Policy or Terms of Service link in the footer
- **THEN** the corresponding legal page is displayed

### Requirement: SEO and discoverability
The system SHALL make public pages discoverable by search engines with per-page metadata and standard crawler files.

#### Scenario: Per-page metadata
- **WHEN** any public page is rendered
- **THEN** it includes a descriptive `<title>`, meta description, and Open Graph tags for social sharing

#### Scenario: Sitemap and robots
- **WHEN** a crawler requests `/sitemap.xml` or `/robots.txt`
- **THEN** a valid sitemap listing public pages and a robots file are served

### Requirement: Responsive and accessible public site
The system SHALL present the public website usably on phones, tablets, and desktops with basic accessibility.

#### Scenario: Mobile layout
- **WHEN** a visitor opens any public page on a phone
- **THEN** content and navigation are usable without horizontal scrolling

#### Scenario: Basic accessibility
- **WHEN** a visitor uses a screen reader or keyboard navigation
- **THEN** images have alt text, form fields have labels, and interactive elements are keyboard reachable
