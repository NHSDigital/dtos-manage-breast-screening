# ADR-007: Creating an endpoint for Batch data from BS Select

## Context

The Cohort to Clinic team are looking to build functionality to select Participants and place them in Appointments.

We’ve made the decision to pick up the service from the point at which a Batch is created in BS Select, and start to fill in the gaps between that stage, up to where the Manage team’s work is being done for on-the-day screening features. [Some future state thinking here.](https://nhsd-confluence.digital.nhs.uk/spaces/DTS/pages/1336639097/Architectural+design+thinking)

## Decision

### Assumptions

- In order to build an MVP, we need to ingest Batch and Participant data into our service from BS Select. [More info about BS Select’s current architecture here.](https://nhsd-confluence.digital.nhs.uk/pages/viewpage.action?pageId=293240926&spaceKey=BSS&title=BS-Select%2BData%2BFlows). It makes sense to get a minimal Batch workflow in place so that we can start to understand the complex UX and relationships required to place and invite Participants to Clinic Slots/Appointments.
- We are assuming for an MVP/alpha/private beta phase we will be dual-running with NBSS and all necessary data input and reporting etc. will still be done through NBSS.
- We will build in the Manage repo, with a view to providing one seamless service to users.
- We have the dev time available now to build out an minimal API.

### Options

#### Option 1: BS Select sends Batches to C2C via REST API (Chosen)

1. In BS Select, a user opts to select and send a Batch.
2. BS Select makes API call to send JSON to both IUVO (NBSS) and a C2C REST endpoint
3. The new Batch is visible in C2C for users within the same BSO, to be manually checked for exceptions and imported by BSO Staff (similar to current NBSS workflow)

Pros:

- Less work for user
- Instant access to data on C2C
- Simple for BS Select to build the logic in a way that could easily be taken out or scaled in future.
- It allows us to get a skeleton journey up and running quickly.

Cons:

- Dev work needed to build both sides of API (but it’s not a huge amount)
- No ability to queue/process asynchronously or to retry automatically (but that could be built in if needed for future.)
- Yet another repository of Batch data is being created. This could be mitigated before going live - e.g. if we have an end-to-end flow then a Batch would not have to be sent to NBSS - and we could take a different approach to how we ingest Participant data.

#### Option 2: Manual file upload

1. User downloads a file of Batch data from BS Select
2. User upload to C2C
3. Turn file data into a Batch and Participants in C2C

There is existing functionality to download a CSV once a Batch has been selected – we could use the current file data to present something within C2C.

Pros:

- Little/no dev work required on BS Select side
- Wouldn't have to build any API integrations on C2C side

Cons:

- It’s not a great user experience – it pushes work onto user needing to manage files and switch between contexts.
- Security/validity issues with data needing to be downloaded locally, allows possibility for data to be edited or files to be uploaded more than once.

#### Option 3: API to GET Batches on BS Select

1. BS Select make a REST API endpoint of Batch data
2. C2C can GET a list of Batches based on BSO – user can choose which Batches to import

Pros:

- Less work for user
- Instant access to data on C2C
- Compared to B, we wouldn't need to build an endpoint on C2C, just request the data

Cons:

- Dev work needed on BS Select side – it would be quite a change to their data flows potentially.
- BS Select and even Batches themselves are potentially not going to be used in a longer term vision for the service, so we don't want to invest too much time on new functionality.
- It's a bit less clean cut of an event when a batch has been selected and chosen to use in Manage, whereas with option B we would have an event timestamp and audit trail for when the Batch is created and sent over.

### Outcome

Option 1. As both BS Select and C2C have the capacity to make the changes needed to send Batches to a C2C API in the short term, it would be worth us building out this functionality – it may not be the perfect solution to synchronise data between the two systems, or the most minimal compared to using a file upload, but it would still be a small change to existing data flows, whilst still providing some improvements for the user. We could build on the integration once it’s setup, this is a chance to lay some initial pipes.

## Consequences

We can start building an API endpoint in Manage for the BS Select team to POST to, behind a feature flag, conforming to any existing patterns as much as possible in Manage - such as using NinjaAPI. We can then provide a spec for BS Select to start sending over data in a test environment.
