# ADR-006: Gateway API versioning strategy

## Context

The Manage service exposes an HTTP API used by the gateway. The gateway sends DICOM image data and failure reports to Manage via this API.

The API is currently at v1, mounted at `/api/v1/`. As the system evolves, API changes will be necessary. Because the gateway is deployed on-premises at individual hospital sites, Manage and gateway deployments will not always be synchronised. The API therefore needs a versioning strategy that allows both sides to evolve without requiring simultaneous deployment.

## Decision

### Assumptions

- The gateway is the only consumer of this API.
- There is a single gateway codebase, but many deployed instances across hospital sites.
- Hospital IT teams may control when gateway updates are applied, meaning deployed instances may lag behind the latest release.
- Django Ninja is used to implement the API, which supports multiple `NinjaAPI` instances mounted at different URL prefixes.

### Drivers

- Manage and gateway deployments must be partially decoupled.
- The API contract should be clearly defined and versioned so that breaking changes can be introduced safely.
- Complexity should be kept proportionate to actual need — over-engineering versioning infrastructure for a single consumer codebase is wasteful.

### Options

#### Option 1: URL-based major versioning with major.minor convention (chosen)

Use a URL prefix for the major version (`/api/v1/`, `/api/v2/`). Adopt a `major.minor` convention for communicating the nature of changes:

- **Non-breaking changes** (new endpoints, new optional fields): increment the minor version in the OpenAPI `version` string (e.g. `1.0` → `1.1`). The URL does not change.
- **Breaking changes** (removed or renamed fields, changed behaviour, new required parameters): increment the major version and mount a new `NinjaAPI` instance at the new URL prefix (e.g. `/api/v2/`). The previous major version URL is kept alive for a deprecation period (broadly speaking, until it becomes annoying and pointless to maintain it).

#### Option 2: URL-based major versioning with pinned minor version URLs

As Option 1, but also expose pinned minor version URLs (e.g. `/api/v1.1/`) so consumers can opt in to a specific minor version and avoid unexpected changes from non-breaking additions.

Given there is a single consumer codebase, pinned minor version URLs add URL routing and documentation complexity with no practical benefit — a well-implemented consumer should be tolerant of new optional fields and endpoints.

#### Option 3: Header-based versioning (`Accept` or custom header)

Version communicated via a request header rather than the URL. Less discoverable, harder to test manually, and not the established convention in NHS Digital services.

### Outcome

Option 1. URL-based major versioning with a `major.minor` convention. This is a reversible decision — if the need for pinned minor version URLs arises (e.g. a second consumer is added), Option 2 can be adopted as a straightforward extension.

### Rationale

The URL is the natural and conventional place for an API version. The `major.minor` convention communicates clearly to developers and operators what kind of change has occurred. Pinned minor version URLs (Option 2) are YAGNI given a single consumer codebase.

## Consequences

- When a breaking change is made to the API, a new `NinjaAPI` instance must be created in `core/api.py` and mounted at the new version prefix in `core/urls.py`. The previous version must be kept alive until all gateway instances in the field have been updated.
- Non-breaking changes require only a minor version bump to the `version=` string in the `NinjaAPI` constructor.
- The deprecation period for an old major version is determined operationally: it should remain available until confidence is high that all deployed gateway instances have been updated. Given hospital IT teams may control update schedules, this window may be longer than a typical SaaS deployment.
- If a second API consumer is introduced in future, the pinned minor version URL approach (Option 2) should be revisited.

## Compliance

Changes to the API should be accompanied by a minor or major version bump as appropriate. Code review is the primary mechanism for enforcing this.

## Notes

- Current API: `v1`, mounted at `/api/v1/` in `manage_breast_screening/core/urls.py`.
- Django Ninja `NinjaAPI(version="1.0.0")` in `manage_breast_screening/core/api.py`.

## Actions

- [ ] Bump the minor version in `NinjaAPI(version=...)` whenever a non-breaking change is made to the API.
