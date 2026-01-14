# ADR 005: User attribution on immutable state records

## Context

The manage breast screening service requires the ability to attribute actions to users for functional purposes e.g. displaying the name of the mammographer that is carrying out the mammogram. This means the application needs to know which user performed certain actions so it can display this information in the user interface, implement business rules, or support clinical workflows.

In ADR-004, we implemented custom audit logging for security and compliance purposes. That ADR made an explicit decision that audit logs should be used for investigation only, not for application functionality. The reasons for this decision were:

- Audit logs may be archived, pruned, or moved to separate storage for compliance reasons
- Application functionality should not depend on data that might be removed or relocated
- Clear separation of concerns: audit data serves compliance/security needs, not functional needs

This leaves us with a question: how do we handle user attribution for functional purposes?

Within our application, we have two types of data:

1. **Mutable records**: Records that can be updated over time (e.g., a `Participant` record where or some attributes may be updated on the same record)
2. **Immutable state records**: Records that represent a point-in-time state transition and are never modified once created (e.g., `AppointmentStatus` records that track the progression of an appointment through states like SCHEDULED, CHECKED_IN, SCREENED)

For mutable records, simply adding a `user_id` field would be problematic. The field would only show the last user who modified the record, losing all historical context about who made which changes.

For immutable state records, the situation is different. These records naturally preserve history because they are never modified. Each status transition creates a new record, building a complete timeline. Adding a `user_id` field to these records provides exactly what we need for functional attribution without additional complexity.

Currently, we have `AppointmentStatus` as our first immutable state record model (We also have `ClinicStatus` but no understanding of attribution requirements of that as yet). An appointment progresses through states (SCHEDULED, CHECKED_IN, SCREENED, etc.), and each transition creates a new `AppointmentStatus` record. In the future, we anticipate similar patterns for other workflows e.g.:

- Image reading workflow: States like AwaitingFirstRead, FirstReadCompleted, AwaitingSecondRead, SecondReadCompleted
- Results workflow: States tracking the progression of screening results
- Referral workflow: States tracking referral processing

These future workflows would benefit from the same attribution pattern.

## Decision

We will add a `user_id` foreign key field to immutable state record models, starting with `AppointmentStatus`. This field will reference our `User` model and track which user created each state transition.

### Key characteristics of this approach:

- **Immutable records**: User attribution via direct foreign key is only added to models that represent immutable state transitions
- **Pattern for future workflows**: This pattern will be applied to future state-based models (e.g., image reading states, results states)
- **Functional, not audit**: This data is for functional purposes (displaying in UI, business rules) and is separate from audit logging
- **Required field**: The `user_id` field will be required (not nullable) to ensure attribution is always captured

### Alternatives considered

#### 1. Add user_id to all models (mutable and immutable)

Store a `user_id` foreign key on every model in the application, including mutable records like `Participant`, `Clinic`, etc.

**Pros:**

- Simple, consistent pattern across all models
- Easy to implement - just add the field to the base model
- Always know who last touched any record

**Cons:**

- **Loses historical context**: For mutable records, you only see the last user who modified it, not who made which changes
- **Violates YAGNI**: We have no current functional requirement for attribution on mutable records
- **Forces premature decision**: Commits us to a specific attribution pattern before we understand the requirements
- **Audit confusion**: Might create confusion about the relationship between functional attribution and audit logs

#### 2. Use audit logs for functional purposes

Query the `AuditLog` table to determine who performed actions, rather than storing user attribution directly on functional models.

**Pros:**

- No additional fields needed on models
- Reuses existing audit infrastructure
- Complete historical context is available

**Cons:**

- **Coupling risk**: Application functionality would break if audit logs are archived, pruned, or moved to cold storage
- **Performance concerns**: Querying audit logs for functional UI operations adds unnecessary overhead
- **Separation of concerns**: Mixes security/compliance data with functional application data
- **Different lifecycle**: Audit data may have different retention policies than functional data

See also [ADR-004](ADR-004-Custom_audit_logging.md)

#### 3. Create separate attribution tables

Create dedicated attribution tables (e.g., `AppointmentStatusAttribution`) that track user actions separate from both the main models and audit logs.

**Pros:**

- Clear separation between functional data, attribution, and audit
- Flexible schema for attribution-specific fields (reason, notes, etc.)

**Cons:**

- **Significant over-engineering**: Creates extra complexity for a simple need
- **Additional joins**: Requires extra database joins for every query that needs attribution
- **More tables to maintain**: Additional models, migrations, and schema complexity
- **Violates YAGNI**: We don't have requirements for multiple attributions, approval chains, or attribution-specific metadata
- **Harder to query**: Simple queries like "show me this status and who created it" require joins
- **Pushes integrity maintenance into the application**: makes it possible to create unattributed changes

#### 4. Add user_id to immutable state records (chosen approach)

Add `user_id` directly to immutable state record models like `AppointmentStatus`.

**Pros:**

- **Pragmatic and minimal**: Solves the actual requirement without over-engineering
- **Perfect fit for immutable records**: These records are never updated, so user attribution is complete and never lost
- **Simple queries**: No additional joins needed - the attribution is right on the record
- **Natural pattern**: Each state transition includes "what" (the state), "when" (timestamp), and "who" (user)
- **YAGNI-compliant**: Only builds what we need now, doesn't add unused infrastructure
- **Scalable pattern**: Easy to apply the same approach to future state-based workflows
- **Clear boundaries**: Functional attribution is separate from audit logs, mutable records use different approaches when needed

**Cons:**

- **Pattern inconsistency**: Different models have different attribution approaches (though this reflects different data characteristics)
- **Future decision needed**: When we need attribution on mutable records, we'll need to decide on an approach (though this is appropriate - we can make that decision when we understand the requirements)

## Consequences

### Positive consequences

- Attribution is immediately available when querying state records, no additional joins needed
- No performance overhead from querying separate tables
- Complete attribution history is preserved because records are immutable
- Easy to display in UI: "Status changed to SCREENED by Dr. Smith on 2024-03-15"
- Supports business rules: "Only users who performed first read can see second read results"

### Negative consequences

- Different attribution approaches for different types of models (though this reflects genuine differences in data characteristics)
- Still need to decide how to handle attribution on mutable records if that requirement emerges
- System-generated state transitions may require a designated system user account or alternative handling

## Compliance

Success will be measured by:

- All `AppointmentStatus` records (and future state records) have a valid `user_id`
- UI can display who performed each state transition
- Application can implement user-based business rules without querying audit logs

## Notes

Related code:

- `manage_breast_screening/participants/models/appointment.py` - `AppointmentStatus` model
- Future: Image reading state models
- Future: Results state models

Related ADRs:

- ADR-004: Custom audit logging implementation (establishes that audit logs should not be used for functional purposes)

## Tags

`#data` `#maintainability` `#simplicity` `#functional-requirements`
