# MESH Inbox Polling - Django Notifications App

This module provides functionality to poll the MESH sandbox inbox and store retrieved messages in Azure Blob Storage.

## Overview

The MESH polling system consists of:

- **`mesh_polling.py`**: Core polling and storage logic
- **`management/commands/poll_mesh_inbox.py`**: Django management command
- **Updated `store_new_message()`**: Refactored to use new filename structure

## Configuration

### Django Settings

Add the following settings to your Django settings file:

```python
# MESH Configuration
MESH_BASE_URL = "https://localhost:8700"  # MESH sandbox URL
MESH_MAILBOX_ID = "X26ABC1"               # Your MESH mailbox ID
MESH_CONTAINER_NAME = "mesh-messages"     # Azure Blob container name
MESH_REQUEST_TIMEOUT = 30                 # Request timeout in seconds

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = "your_connection_string_here"
```

### Environment Variables (Fallback)

If not set in Django settings, the system will fall back to environment variables:

```bash
export AZURE_STORAGE_CONNECTION_STRING="your_connection_string_here"
```

### Default Values

If no configuration is provided, the system uses these sensible defaults:

- `MESH_BASE_URL`: `https://localhost:8700`
- `MESH_MAILBOX_ID`: `X26ABC1`
- `MESH_CONTAINER_NAME`: `mesh-messages`
- `MESH_REQUEST_TIMEOUT`: `30` seconds

## Usage

### Django Management Command

Run the polling process using Django's management command:

```bash
python manage.py poll_mesh_inbox
```

### Direct Function Call

You can also call the function directly from your Django code:

```python
from manage_breast_screening.notifications.mesh_polling import run_mesh_polling

# Run the polling process
run_mesh_polling()
```

### Legacy Function

The refactored `store_new_message()` function is available for backward compatibility:

```python
from manage_breast_screening.notifications.mesh_polling import store_new_message

# Store a message with new filename structure
store_new_message(blob_client, message)
```

## Filename Structure

Messages are stored in Azure Blob Storage with the format:

```
yyyy-MM-dd/BSOCODE_TIMESTAMP.dat
```

Where:
- `BSOCODE` is extracted from the first three letters of the message filename
- `TIMESTAMP` is the current datetime in format `YYYYMMDDTHHMMSS`

Example: `2024-01-15/BSO_20240115T143022.dat`

## Logging

The system provides comprehensive structured logging including:

### Log Levels
- **INFO**: Normal operations (connections, successful operations)
- **ERROR**: Failures and exceptions

### Structured Log Data
All log messages include relevant context data:

```python
# Example log entry
{
    "message": "Successfully stored message to blob",
    "blob_name": "2024-01-15/BSO_20240115T143022.dat",
    "bso_code": "BSO",
    "message_id": "BSO_20240115T143022",
    "content_size": 1024,
    "container": "mesh-messages"
}
```

### Key Log Events
- **Connection events**: Azure storage connections
- **API calls**: MESH inbox polling and message retrieval
- **Storage operations**: Blob uploads with metadata
- **Process summary**: Overall success/failure statistics

## Error Handling

The system includes comprehensive error handling for:

- Azure Blob Storage connection failures
- MESH inbox retrieval failures
- Message content retrieval failures
- Blob upload failures
- Network timeouts (configurable)

All errors are logged with structured data for debugging and monitoring.

## Security Features

- **Request timeouts**: Configurable timeout prevents hanging requests
- **SSL verification**: Disabled only for local sandbox (configurable)
- **Connection string security**: Uses Django settings or environment variables
- **Error sanitisation**: Sensitive data is not logged

## Dependencies

The following dependencies have been added to `pyproject.toml`:

- `azure-storage-blob (>=12.19.0,<13.0.0)`
- `requests (>=2.31.0,<3.0.0)`

## Testing

The MESH polling system includes comprehensive testing with multiple approaches:

### Unit Tests (Mocked)

**Fast, reliable tests that work everywhere:**

```bash
# Run all unit tests (mocked - no external dependencies)
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v

# Run with Django test runner
poetry run python manage.py test manage_breast_screening.notifications.tests.test_mesh_polling -v 2
```

**What's tested:**
- ✅ All business logic
- ✅ Error handling
- ✅ Configuration management
- ✅ File naming logic
- ✅ Django integration

**What's mocked:**
- HTTP requests to MESH API
- Azure Blob Storage operations
- External dependencies

**Requirements:**
- ✅ **NO MESH client needed** - All requests are mocked
- ✅ **NO Azure connection needed** - All storage operations are mocked
- ✅ **Works in any environment** - CI/CD, local, production

### Integration Tests (Real MESH Client)

**Tests that validate real API integration:**

```bash
# Run integration tests (requires MESH client running)
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -v

# Run only integration tests with marker
poetry run pytest -m integration -v
```

**What's tested:**
- ✅ Real MESH API connectivity
- ✅ Actual API response structures
- ✅ End-to-end integration
- ✅ Network timeouts and errors

**Requirements:**
- ❌ **MESH client IS needed** - Makes real HTTP requests
- ✅ **Gracefully skips** - When MESH client unavailable
- ✅ **Conditional execution** - Only runs when MESH available

### Test Execution Strategies

#### 1. **CI/CD Pipeline (Recommended)**
```bash
# Run only unit tests - fast and reliable
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v
```

#### 2. **Local Development**
```bash
# Run unit tests
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v

# Run integration tests (if MESH client available)
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -v
```

#### 3. **Selective Testing**
```bash
# Run specific test classes
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py::TestMeshPollingFunctions -v

# Run specific test methods
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py::TestMeshPollingFunctions::test_get_mesh_inbox_messages_success -v
```

### Test Coverage

| Test Type | Coverage | Speed | MESH Client | Azure Connection | Use Case |
|-----------|----------|-------|-------------|------------------|----------|
| **Unit Tests** | Business Logic | Fast | ❌ Not needed (mocked) | ❌ Not needed (mocked) | CI/CD, Development |
| **Integration Tests** | API Integration | Slow | ✅ Required (real) | ❌ Not needed (mocked) | Local Validation |

### Environment-Specific Testing

#### **Local Development**
```bash
# Start MESH client locally
# Then run both test suites
poetry run pytest manage_breast_screening/notifications/tests/ -v
```

#### **CI/CD Pipeline**
```bash
# Only unit tests - no external dependencies
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_polling.py -v
```

#### **Production Validation**
```bash
# Run integration tests against staging MESH
MESH_BASE_URL=https://staging-mesh.example.com poetry run pytest -m integration -v
```

### Test Configuration

#### **Environment Variables for Testing**
```bash
# Enable integration tests
export RUN_MESH_INTEGRATION_TESTS=true

# Override MESH URL for testing
export MESH_BASE_URL=https://test-mesh.example.com

# Set test timeout
export MESH_REQUEST_TIMEOUT=10
```

#### **Django Settings for Testing**
```python
# settings_test.py
MESH_BASE_URL = "https://localhost:8700"
MESH_MAILBOX_ID = "TEST_MAILBOX"
MESH_REQUEST_TIMEOUT = 5  # Shorter timeout for tests
```

### Troubleshooting Tests

#### **Integration Tests Skipped**
If integration tests are being skipped:
```bash
# Check if MESH client is running
curl -k https://localhost:8700/health

# Check configuration
python manage.py shell -c "from django.conf import settings; print(settings.MESH_BASE_URL)"
```

#### **Test Failures**
```bash
# Run with verbose output
poetry run pytest manage_breast_screening/notifications/tests/ -v -s

# Run with debug logging
poetry run pytest manage_breast_screening/notifications/tests/ --log-cli-level=DEBUG
```

### Best Practices

1. **Always run unit tests** - They're fast and reliable
2. **Run integration tests locally** - Before deploying changes
3. **Use CI/CD for unit tests only** - Avoid external dependencies
4. **Mock external services** - For predictable test results
5. **Test error conditions** - Network failures, timeouts, etc.

## Future Enhancements

This implementation is designed to be easily extended for:

- Scheduled polling using Django Celery or similar
- Webhook-based processing instead of polling
- Integration with Django models for message tracking
- Retry logic for transient failures
- Async/await for improved performance
- Connection pooling for Azure operations
