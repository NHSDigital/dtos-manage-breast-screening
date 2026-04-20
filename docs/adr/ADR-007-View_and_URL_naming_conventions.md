# ADR-007: View and URL naming conventions

> |              |             |
> | ------------ | ----------- |
> | Date         | 20/04/2026  |
> | Status       | Accepted    |
> | Deciders     | Engineering |
> | Significance | Structure   |
> | Owners       | MBS devs    |

---

- [ADR-007: View and URL naming conventions](#adr-007-view-and-url-naming-conventions)
  - [Context](#context)
  - [Decision](#decision)
    - [View classes](#view-classes)
    - [View functions](#view-functions)
    - [URL paths](#url-paths)
    - [URL names](#url-names)
    - [File names](#file-names)
  - [Consequences](#consequences)

## Context

As the codebase has grown, inconsistencies emerged in how views, URL paths, URL names, and view files were named. Views used varying verb prefixes (`ChangeLumpView`, `RecordMedicalInformation`). URL names mixed `change_*` and `update_*`. Some view classes had the `*View` suffix, others didn't.

Consistent conventions reduce cognitive overhead when navigating the codebase and make the intent of a view or URL immediately clear.

## Decision

### View classes

Prefer the pattern `{Verb}{ResourceNoun}View`, where the verb is one of `Add`, `Update`, `Upsert`, `Delete`, `Show` or `List`:

```
AddBenignLumpHistoryItemView
UpdateBenignLumpHistoryItemView
DeleteBenignLumpHistoryItemView
ShowAppointmentView
ListClinicsView
```

The `Upsert` prefix is for any view that handles both add and update actions.

For views that don't map cleanly to a CRUD operation, use `{Verb}{DomainConcept}View` instead, where the verb succinctly describes the functionality being handled:

```
ConfirmAppointmentProceedAnywayView
MarkSectionReviewedView
PauseAppointmentView
```

### View functions

Align with the class naming convention where it makes sense. Add a `_view` suffix to function names. If a function-based view grows in complexity, consider converting it to a class-based view.

```python
def check_information_view(request, pk): ...
def attended_not_screened_view(request, appointment_pk): ...
def list_clinics_view(request, filter="today"): ...
```

### URL paths

Use hyphens for multi-word path segments. All paths must have a trailing slash. For singleton resources (at most one instance per parent), omit the child ID:

```
/mammograms/<uuid>/note/add/          ← singleton: no note ID
```

Standard CRUD patterns:

| HTTP Method | URL Pattern           | URL Name      | View Class       | Example                      |
| ----------- | --------------------- | ------------- | ---------------- | ---------------------------- |
| GET         | `/nouns/`             | `noun_list`   | `NounListView`   | `/clinics/`                  |
| GET         | `/nouns/<id>/`        | `show_noun`   | `ShowNounView`   | `/mammograms/<id>/`          |
| GET/POST    | `/nouns/add/`         | `add_noun`    | `AddNounView`    | `/skin-changes/add/`         |
| GET/POST    | `/nouns/<id>/update/` | `update_noun` | `UpdateNounView` | `/skin-changes/<id>/update/` |
| GET/POST    | `/nouns/<id>/delete/` | `delete_noun` | `DeleteNounView` | `/skin-changes/<id>/delete/` |

For nested resources:

| HTTP Method | URL Pattern                                 | View Class        |
| ----------- | ------------------------------------------- | ----------------- |
| GET/POST    | `/parents/<id>/children/add/`               | `AddChildView`    |
| GET/POST    | `/parents/<id>/children/<child_id>/update/` | `UpdateChildView` |
| GET/POST    | `/parents/<id>/children/<child_id>/delete/` | `DeleteChildView` |

Paths that dont' fit a resource-oriented pattern should use judgement and align with the name of the view they map to.

### URL names

URL names should be snake_case and mirror the view name:

```
update_image_details  →  UpdateImageDetailsView
add_symptom_lump      →  AddSymptomLumpView
```

### File names

All files containing view classes or functions must have the suffix `_views`, using the plural form even when the file contains only one class:

```
appointment_workflow_views.py
symptom_views.py
```

Following Django conventions, start with `views.py` and extract cohesive groups into separate files as the module grows (e.g. `appointment_workflow_views.py`, `symptom_views.py`, `/medical_history`).

## Consequences

- Non-CRUD views require judgement on naming; the `{DomainConcept}View` fallback is intentionally permissive to avoid forcing awkward verb prefixes onto views that don't fit the pattern.
