# MESH Polling Management Command

This command polls the MESH inbox for new messages, retrieves their content, and stores them in Azure Blob Storage.

## Module Structure

The MESH functionality is organised into separate modules for better maintainability:

- **`mesh/`** - MESH API integration and polling logic
  - `polling.py` - Core MESH polling functionality
  - `tests/` - Unit tests for MESH functionality
- **`storage/`** - Azure Blob Storage operations
  - `azure.py` - Azure Blob Storage client and operations
  - `tests/` - Unit tests for storage functionality

## Configuration

Add the following settings to your Django settings file:

```python
# MESH Configuration
MESH_BASE_URL = os.getenv('MESH_BASE_URL', 'https://localhost:8700')
MESH_MAILBOX_ID = os.getenv('MESH_MAILBOX_ID', 'X26ABC1')
MESH_USERNAME = os.getenv('MESH_USERNAME', '')
MESH_PASSWORD = os.getenv('MESH_PASSWORD', '')

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')
AZURE_STORAGE_CONTAINER_NAME = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'mesh-messages')
```

## Usage

Run the command to poll the MESH inbox:

```bash
python manage.py poll_mesh_inbox
```

## Features

- **Automatic polling** of MESH inbox for new messages
- **Message content retrieval** for each message ID
- **Azure Blob Storage integration** with structured filename format
- **Comprehensive logging** with structured log messages
- **Error handling** with retry logic for transient failures
- **BSO code extraction** from message IDs for filename organisation

## File Storage Format

Messages are stored in Azure Blob Storage with the following structure:

```
container/
├── 2024-01-15/
│   ├── BSO_20240115T143022.dat
│   ├── ABC_20240115T143045.dat
│   └── XYZ_20240115T143108.dat
└── 2024-01-16/
    ├── BSO_20240116T091234.dat
    └── DEF_20240116T091256.dat
```

Where:
- `YYYY-MM-DD/` - Date-based folder structure
- `BSO_TIMESTAMP.dat` - Filename with BSO code and timestamp
- BSO code is extracted from the first 3 characters of the message ID

## Testing

The MESH polling system includes comprehensive testing with multiple approaches:

### Unit Tests (Mocked - Recommended for CI/CD)

**Fast, reliable tests that work everywhere:**

```bash
# Test MESH polling functionality
python manage.py test manage_breast_screening.notifications.mesh.tests

# Test Azure storage functionality
python manage.py test manage_breast_screening.notifications.storage.tests

# Run with pytest for more detailed output
poetry run pytest manage_breast_screening/notifications/mesh/tests/ -v
poetry run pytest manage_breast_screening/notifications/storage/tests/ -v
```

**What's tested:**
- All business logic
- Error handling
- Configuration management
- File naming logic
- Django integration

**What's mocked:**
- HTTP requests to MESH API
- Azure Blob Storage operations
- External dependencies

**Requirements:**
- **NO MESH client needed** - All requests are mocked
- **NO Azure connection needed** - All storage operations are mocked
- **Works in any environment** - CI/CD, local, production

### Integration Tests (Real MESH Client)

**Tests that validate real API integration:**

```bash
# Run integration tests (requires MESH client running)
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -v

# Run only integration tests with marker
poetry run pytest -m integration -v
```

**What's tested:**
- Real MESH API connectivity
- Actual API response structures
- End-to-end integration
- Network timeouts and errors

**Requirements:**
- **MESH client IS needed** - Makes real HTTP requests
- **Gracefully skips** - When MESH client unavailable
- **Conditional execution** - Only runs when MESH available

### Test Execution Strategies

#### 1. **CI/CD Pipeline (Recommended)**
```bash
# Run only unit tests - fast and reliable
poetry run pytest manage_breast_screening/notifications/mesh/tests/ manage_breast_screening/notifications/storage/tests/ -v
```

#### 2. **Local Development**
```bash
# Run unit tests
poetry run pytest manage_breast_screening/notifications/mesh/tests/ manage_breast_screening/notifications/storage/tests/ -v

# Run integration tests (if MESH client available)
poetry run pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -v
```

#### 3. **Selective Testing**
```bash
# Run specific test classes
poetry run pytest manage_breast_screening/notifications/mesh/tests/test_polling.py::TestMeshPollingFunctions -v

# Run specific test methods
poetry run pytest manage_breast_screening/notifications/mesh/tests/test_polling.py::TestMeshPollingFunctions::test_get_mesh_inbox_messages_success -v
```

### Test Coverage

| Test Type | Coverage | Speed | MESH Client | Azure Connection | Use Case |
|-----------|----------|-------|-------------|------------------|----------|
| **Unit Tests** | Business Logic | Fast | Not needed (mocked) | Not needed (mocked) | CI/CD, Development |
| **Integration Tests** | API Integration | Slow | Required (real) | Not needed (mocked) | Local Validation |

### Environment-Specific Testing

#### **Local Development**
```bash
# Start MESH client locally
# Then run both test suites
poetry run pytest manage_breast_screening/notifications/mesh/tests/ manage_breast_screening/notifications/storage/tests/ manage_breast_screening/notifications/tests/test_mesh_integration.py -v
```

#### **CI/CD Pipeline**
```bash
# Only unit tests - no external dependencies
poetry run pytest manage_breast_screening/notifications/mesh/tests/ manage_breast_screening/notifications/storage/tests/ -v
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

## Error Handling

The command includes comprehensive error handling:

- **Network timeouts** - Retry with exponential backoff
- **Authentication failures** - Log error and continue
- **Storage errors** - Log error and continue processing other messages
- **Invalid message formats** - Skip problematic messages and continue

## Logging

The command uses structured logging with the following log levels:

- **INFO** - Normal operation messages
- **WARNING** - Non-critical issues (e.g., no messages found)
- **ERROR** - Critical failures that prevent processing
- **DEBUG** - Detailed debugging information

## Dependencies

Required packages (already included in project dependencies):
- `requests` - HTTP client for MESH API calls
- `azure-storage-blob` - Azure Blob Storage client
- `django` - Django framework integration

## Future Enhancements

This implementation is designed to be easily extended for:

- Scheduled polling using Django Celery Beat or similar
- Webhook-based processing instead of polling
- Integration with Django models for message tracking
- Retry logic for transient failures
- Async/await for improved performance
- Connection pooling for Azure operations
