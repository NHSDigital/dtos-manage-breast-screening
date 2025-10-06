# ADR 004: Custom audit logging implementation

## Context

The manage breast screening service handles sensitive personal data that requires robust audit capabilities. We need the ability to track changes to data stored by the application, enabling us to quickly understand what happened in the event of an unauthorised change, data corruption, or bug in the application.

As a healthcare application, we have specific audit requirements:

- Track WHO made changes (user or system process)
- Track WHAT changed (model, operation, and field-level snapshots)
- Track WHEN changes occurred
- Support both user-driven and automated system updates
- Enable investigation of data integrity issues

We are conscious that this data can grow rapidly and need to consider future archiving or pruning.

We initially explored using existing Django audit libraries but found they did not fully meet our needs.

## Decision

We decided to implement a custom audit logging solution consisting of:

1. A single `AuditLog` model that captures audit events across all models
2. An `Auditor` service class that explicitly logs audit events
3. Explicit audit calls at the application/service layer rather than automatic tracking via model signals

### Key characteristics of our implementation:

- **Explicit auditing**: Developers must explicitly call `auditor.audit_create()`, `auditor.audit_update()`, or `auditor.audit_delete()` to create audit logs
- **Single audit table**: All audit records are stored in one `AuditLog` table using Django's `ContentType` framework to identify the audited model
- **JSON snapshots**: Field-level data is captured as JSON snapshots (excluding configured fields like passwords)
- **Actor tracking**: Records either the authenticated user or a system update identifier
- **Bulk operation support**: Provides `audit_bulk_create()`, `audit_bulk_update()`, and `audit_bulk_delete()` methods
- **Integration at service layer**: Audit calls are made in form handlers and service methods, not at the ORM level

### Alternatives considered

We initially attempted to use `django-simple-history` (PR #109), which was ultimately rejected in favour of the custom implementation.

#### django-simple-history approach

django-simple-history works by:

- Creating a separate history table for each model (e.g. `HistoricalClinic`, `HistoricalPatient`)
- Automatically capturing changes via Django's `post_save`, `pre_save`, and `post_delete` signals
- Using middleware to capture the current user and attach it to history records
- Providing a `HistoricalRecords` manager on each model

**Pros:**

- Well-maintained, established library (48 releases, tested against Django 5.2)
- Automatic audit trail with minimal boilerplate
- Built-in Django admin integration via `SimpleHistoryAdmin`
- Can revert models to previous versions
- Good documentation

**Cons:**

- **Opaque**: Signal-based auditing can miss certain operations (bulk creates, bulk updates, raw SQL, direct database updates)
- **Implicit**: Developers might not realise when audit logging is or isn't happening
- **Database complexity**: Creates a separate history table for each audited model, leading to many migration files and complex schema
- **Limited control**: Difficult to audit operations that don't go through standard model save/delete paths
- **Performance overhead**: Signals fire on every save, even when you might not need auditing
- **Migration burden**: Each model change requires migrations for both the model and its history table

#### Other libraries evaluated

- **django-auditlog**: Similar to django-simple-history but less well maintained (11 releases vs 48, tested against Django 5.1 vs 5.2). Uses a single audit table but still relies on automatic signal-based tracking.
- **django-reversion**: More focused on version control and rollback functionality rather than audit logging. Lighter documentation and not tested against latest Django (5.0 vs 5.2).
- **pgAudit**: SQL-level solution that would require PostgreSQL-specific configuration and wouldn't integrate well with Django ORM.

### Rationale

We chose the custom implementation over django-simple-history and other libraries because:

1. **Reliability**: Explicit audit calls ensure we don't accidentally miss auditing important operations. With signal-based approaches, bulk operations, raw SQL, and certain ORM methods can bypass audit logging entirely.

2. **Transparency**: Developers can see exactly when and what is being audited. There's no "magic" happening behind the scenes that might fail silently.

3. **Simplicity**: A single audit table is easier to query and maintain than per-model history tables. This reduces database complexity and migration overhead.

4. **Flexibility**: We can audit operations that happen outside the normal Django ORM flow, such as:
   - Bulk imports from external systems
   - Data transformations that don't use standard save/delete methods
   - System-driven updates that need to be tracked with a system update ID

5. **Performance control**: We only create audit logs when explicitly needed, avoiding unnecessary overhead from signal handlers firing on every model save.

6. **Healthcare context**: For a healthcare application, we need confidence that our audit trail is complete. The explicit approach makes it easier to verify that all critical operations are audited.

The trade-off is that developers must remember to add audit calls, but we consider this acceptable because:

- It makes auditing a deliberate, reviewed decision
- It's easier to catch missing audit calls in code review than to debug why signal-based auditing failed
- We don't need automatic version tracking or rollback functionality - audit logs are for investigation only

## Consequences

### Positive consequences

- Audit logging is visible and explicit in the codebase
- Single audit table is easier to query for investigations (e.g. "show me all changes by this user" or "show me all changes to this patient")
- Bulk operations are properly supported
- No risk of missing audit logs due to ORM quirks or bulk operations
- Simpler database schema with fewer migration files
- Can audit system updates that don't have an authenticated user
- Flexible enough to handle edge cases (e.g. auditing before delete to capture the object ID)

### Negative consequences

- Developers must remember to add explicit audit calls when implementing new features
- More boilerplate code compared to automatic solutions
- No built-in rollback/revert functionality (though we don't need this)
- Need to maintain custom audit code rather than relying on a third-party library

### Mitigation strategies

To address the risk of forgetting to add audit calls:

- Code review checklist should include verifying audit calls for data modifications
- Integration tests should verify that audit logs are created for critical operations
- The `Auditor` class validates that either a user or system update ID is provided (currently commented out until authentication is implemented)

### Future considerations

- Once authentication is fully implemented, uncomment the `AnonymousAuditError` check in the `Auditor` constructor
- Consider audit log retention policies (how long to keep audit records)
- May want to add helper methods to common model operations to reduce boilerplate
- Could add linting rules to detect model saves without corresponding audit calls

## Compliance

Success will be measured by:

- All data modification operations in production have corresponding audit log entries
- Audit logs can be successfully used to investigate data integrity issues
- Audit trail is complete enough to satisfy information governance requirements

## Notes

Related code:

- `manage_breast_screening/core/models.py` - `AuditLog` model definition
- `manage_breast_screening/core/services/auditor.py` - `Auditor` service class
- `manage_breast_screening/config/settings.py` - `AUDIT_EXCLUDED_FIELDS` configuration

Related pull requests:

- PR #109: Initial attempt with django-simple-history (closed)
- PR #120: Final implementation with custom audit logging (merged)

## Tags

`#security` `#data` `#maintainability` `#reliability`
