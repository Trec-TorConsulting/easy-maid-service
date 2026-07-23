## ADDED Requirements

### Requirement: Isolated Frappe/ERPNext instance
The system SHALL run as a new, dedicated Frappe + ERPNext instance that is fully isolated from the existing `frappe` namespace and site `client.trector.com`. The instance MUST run image `frappe/erpnext:version-16` and MUST NOT share the database, Redis, storage, or site of any other instance.

#### Scenario: New namespace is isolated
- **WHEN** the platform is deployed
- **THEN** all resources are created in the `easymaid` Kubernetes namespace
- **AND** no resource references or mutates anything in the `frappe` namespace

#### Scenario: Existing instance untouched
- **WHEN** the new instance is deployed or torn down
- **THEN** the existing `frappe` site `client.trector.com` continues to serve unchanged

### Requirement: Data and cache services
The system SHALL provision MariaDB 10.11 for the database and three Redis 7.2 instances (cache, queue, socketio), each dedicated to this instance.

#### Scenario: Database is provisioned
- **WHEN** the platform starts
- **THEN** a MariaDB 10.11 StatefulSet is running with a Longhorn RWO persistent volume
- **AND** its root/app credentials are sourced from a Kubernetes Secret, never hardcoded in manifests

#### Scenario: Redis roles are separated
- **WHEN** the platform starts
- **THEN** separate Redis 7.2 services exist for cache, queue, and socketio

### Requirement: Application workloads
The system SHALL run the Frappe web/API server, socketio server, background workers, and scheduler as separate workloads.

#### Scenario: Core workloads run
- **WHEN** the platform is healthy
- **THEN** the Frappe web/API deployment serves HTTP on port 8000
- **AND** the socketio deployment serves on port 9000
- **AND** at least one background worker and the scheduler are running

### Requirement: Persistent site storage
The system SHALL store site files on a Longhorn ReadWriteMany persistent volume so multiple pods can share the sites directory.

#### Scenario: Sites volume is shared
- **WHEN** more than one Frappe pod is scheduled
- **THEN** all pods mount the same RWX `sites` PersistentVolumeClaim backed by Longhorn

### Requirement: Ingress and TLS
The system SHALL expose the site at `easymaid.trector.com` via Traefik with automatic TLS from the `letsencrypt` cert resolver, redirecting HTTP to HTTPS.

#### Scenario: HTTPS is served
- **WHEN** a user requests `https://easymaid.trector.com`
- **THEN** Traefik routes `/` to the Frappe web service and `/socket.io` to the socketio service over a valid Let's Encrypt certificate

#### Scenario: HTTP is redirected
- **WHEN** a user requests `http://easymaid.trector.com`
- **THEN** the request is permanently redirected to the HTTPS URL

### Requirement: Node scheduling constraints
The system SHALL schedule all workloads away from GPU/video-reserved nodes.

#### Scenario: Reserved nodes are excluded
- **WHEN** any platform pod is scheduled
- **THEN** node affinity excludes `node05` and `node06`

### Requirement: Site bootstrap and app install
The system SHALL create the new site and install ERPNext and the custom `easy_maid` app via an initialization Job.

#### Scenario: Site is created with apps
- **WHEN** the site-init Job runs on a fresh instance
- **THEN** it runs `bench new-site` for the instance site with admin credentials from a Secret
- **AND** installs `erpnext` and `easy_maid`
- **AND** the Job is idempotent (re-running does not corrupt or duplicate the site)

### Requirement: Resilience and backups
The system SHALL protect availability with Pod Disruption Budgets and SHALL back up the database and site files on a schedule.

#### Scenario: Disruption budgets exist
- **WHEN** a voluntary disruption occurs
- **THEN** PDBs keep at least one replica of the web server and database available

#### Scenario: Scheduled backups run
- **WHEN** the backup schedule fires
- **THEN** a database + files backup is produced and retained for the configured retention window
