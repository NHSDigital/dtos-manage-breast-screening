# ADR-005: Enforce provider-scoped queries for sensitive healthcare data

> |              |                           |
> | ------------ | ------------------------- |
> | Date         | 28/10/2025                |
> | Status       | Accepted                  |
> | Deciders     | Dev Team                  |
> | Significance | Security, Data, Structure |
> | Owners       | @malcolmbaig              |

---

- [ADR-005: Enforce provider-scoped queries for sensitive healthcare data](#adr-005-enforce-provider-scoped-queries-for-sensitive-healthcare-data)
  - [Context](#context)
  - [Decision](#decision)
    - [Assumptions](#assumptions)
    - [Options](#options)
      - [Option 1: Queryset scopes via `for_provider`](#option-1-queryset-scopes-via-for_provider)
      - [Option 2: Provider properties with filtered querysets](#option-2-provider-properties-with-filtered-querysets)
      - [Option 3: Repository pattern](#option-3-repository-pattern)
    - [Outcome](#outcome)
    - [Rationale](#rationale)
  - [Consequences](#consequences)
    - [Positive consequences](#positive-consequences)
    - [Negative consequences](#negative-consequences)
    - [Mitigation strategies](#mitigation-strategies)

## Context

The Manage Breast Screening application is a multi-tenanted healthcare system handling sensitive patient data across multiple healthcare providers. Each provider must only have access to their own participants, appointments, and clinic data.

Without explicit provider-scoping at the data access layer, there is a risk that we expose data from one provider to users of another provider. This could happen, for example:

- Via a bug in our view logic
- A user accessing a bookmarked page for a provider they no longer have access to

We also need some level of automated enforcement of this scoping to catch any instances where we forget to apply it.

## Decision

### Assumptions

- The Provider model represents the primary boundary for data access control
- All users have an associated `current_provider` accessible via `request.current_provider`
- The three most sensitive data models requiring protection are `Appointment`, `Clinic`, and `Participant`
- CI/CD pipeline can block merges if linting violations are detected
- We can lint for usage of Model.objects and helpers such as get_object_or_404 - assume all options will be paired with a linter of this sort

### Options

#### Option 1: Queryset scopes via `for_provider`

Expose a `.for_provider(provider)` scope on each sensitive model's queryset/manager and require views to call it explicitly.

**Example:**

```python
class ClinicQuerySet(models.QuerySet):
    def for_provider(self, provider):
        return self.filter(setting__provider=provider)

class Clinic(models.Model):
    objects = ClinicQuerySet.as_manager()

def clinic_list(request):
    provider = request.current_provider
    clinics = Clinic.objects.for_provider(provider)
```

**Pros:**

- Centralizes scoping logic alongside each model
- Keeps view code close to vanilla Django patterns
- Allows additional queryset filtering to be chained naturally
- Easy to add unit tests for the scope itself

**Cons:**

- Relies on developers remembering to call `for_provider`
- Nothing in this approach discourages developers from simply adding alternative scopes that bypass the provider scoping
- Naming consistency must be maintained across models
- Linter needs to allow Model.objects

#### Option 2: Provider properties with filtered querysets

Add properties to the `Provider` model that return pre-filtered querysets.

**Example:**

```python
class Provider(BaseModel):
    @property
    def appointments(self):
        return Appointment.objects.filter(
            clinic_slot__clinic__setting__provider=self
        )
```

**Pros:**

- Centralizes the scoping logic in one place
- Works naturally with Django's ORM patterns
- Low ceremony - can chain additional filters
- Explicit relationship between provider and data
- Establishes the convention that sensitive data is accessed via a provider instance

**Cons:**

- No strong enforcement mechanism - developers can bypass the properties by adding custom methods to the model managers

#### Option 3: Repository pattern

Introduce provider-scoped repository classes (for example `ClinicRepository`, `AppointmentRepository`, `ParticipantRepository`) that inherit from a shared `ProviderScopedRepository` base. Each repository is initialised with the current provider and exposes explicit methods (`list`, `get` etc) that wrap any additional ordering or eager-loading. Views import these repositories instead of the Django models.

**Example:**

```python
def clinic(request, pk, filter="remaining"):
    clinic_repo = ClinicRepository(request.current_provider)
    clinic = clinic_repo.get(pk)

    appointment_repo = AppointmentRepository(request.current_provider)
    appointments = appointment_repo.list(clinic, filter)
```

**Pros:**

- Constructor requires a provider, making scoping mandatory and difficult to forget.
- Query composition and eager-loading live in one place, so view functions stay minimal and consistent.

**Cons:**

- Introduces an additional abstraction layer that developers must understand and maintain.
- Slightly more setup in views (instantiating repositories) compared with direct manager access.

### Outcome

Option 2.

### Rationale

Option 2 provides a workable solution to the problem without the overhead of additional abstractions introduced by Option 3. By continuing to encourage the use of QuerySets as a place to add querying logic, we also have a pathway to refactor from QuerySet to Repository if a need arises in the future.

1. It achieves the goal of provider scoping at the data access layer
2. It's simple to implement and understand
3. Linter rules detecting model manager and helper usage in views can help catch cases where we aren't accessing sensitive records through the provider

## Consequences

### Positive consequences

1. **Prevention of insecure access**: The provider-scoped pattern makes it harder to accidentally query across provider boundaries in view code
2. **Early detection**: The linter makes it harder to bypass the provider-scoped pattern

### Negative consequences

1. **Additional boilerplate**: Developers must write `request.current_provider.appointments` instead of `Appointment.objects`
2. **New model maintenance**: When adding new sensitive models, must update the linter's denylist

### Mitigation strategies

1. **Code examples**: Existing view code serves as examples of the correct pattern
2. **Code review**: Verify that data access in views makes use of `request.current_provider`
3. **PR templates**: Include a checklist item for verifying provider scoping
