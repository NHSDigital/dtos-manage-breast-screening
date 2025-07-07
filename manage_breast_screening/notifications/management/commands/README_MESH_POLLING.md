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

### Unit Tests

Run unit tests (fully mocked, no external dependencies):

```bash
# Test MESH polling functionality
python manage.py test manage_breast_screening.notifications.mesh.tests

# Test Azure storage functionality
python manage.py test manage_breast_screening.notifications.storage.tests

# Test management command
python manage.py test manage_breast_screening.notifications.tests.test_mesh_integration
```

### Integration Tests

Integration tests require a running MESH client and will be skipped if unavailable:

```bash
# Run all tests including integration tests
python manage.py test manage_breast_screening.notifications.tests.test_mesh_integration

# Run with pytest for selective execution
pytest manage_breast_screening/notifications/tests/test_mesh_integration.py -m integration
```

### Test Coverage

The test suite covers:
- ✅ Core MESH polling functions
- ✅ Azure Blob Storage operations
- ✅ Management command execution
- ✅ Error handling and retry logic
- ✅ Configuration validation
- ✅ Integration scenarios (when MESH client available)

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
