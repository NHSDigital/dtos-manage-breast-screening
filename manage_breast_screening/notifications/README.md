# Manage Breast Screening Notifications

## Notifications App

Notifications is a Django application responsible for sending notifications to clients of the wider Manage Breast Screening project.

The application is composed of a set of Django Admin commands which are run on a schedule.
The commands currently process a feed of data from the active NBSS system.
The commands store and then send appointment notifications via NHS Notify.

Storage is handled via Azure blob containers, Azure storage queues and Postgresql.

Appointment notifications are sent 4 weeks prior to the appointment date.
Any appointment data processed within 4 weeks of the appointment date will also be eligible for notification on the next scheduled batch.

## Running Tests

### End-to-End Tests

To run the end-to-end tests for notifications:

```bash
make test-end-to-end
```

This command will:

- Start the required test dependencies (Azurite, MESH sandbox, and NHS Notify API stub)
- Run the end-to-end test suite
- Clean up the test environment afterwards

The e2e tests are located in `manage_breast_screening/notifications/tests/end_to_end/` and test the complete notification flow from data ingestion through to message sending.

**Prerequisites:**

- Docker must be running
- PostgreSQL database must be available (run `make db` first if needed)

**Troubleshooting:**

- If you get port conflicts, ensure no other MESH sandbox containers are running
- If you get database connection errors, ensure PostgreSQL is running with `make db`

### Integration Tests

To run the integration tests:

```bash
make test-integration
```

### Unit Tests

To run the unit tests for all of Manage:

```bash
make test-unit
```

If you would rather not install all of the JS dependencies and only want to run the Notifications unit tests specifically:

```bash
uv run pytest manage_breast_screening/notifications/tests/ --ignore manage_breast_screening/notifications/tests/dependencies --ignore manage_breast_screening/notifications/tests/integration --ignore manage_breast_screening/notifications/tests/end_to_end
```

This will run only the unit tests for the notifications app, excluding the integration and end-to-end test directories.
