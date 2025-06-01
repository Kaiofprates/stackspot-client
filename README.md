# StackSpot Client Python

A Python client library for interacting with the StackSpot API. This library provides a simple and intuitive interface to authenticate, execute commands, and retrieve results from the StackSpot platform.

## Features

- 🔐 Automatic authentication handling
- 🔄 Automatic token refresh
- ⚡ Retry mechanism for failed requests
- 🛡️ Comprehensive error handling
- 📦 Support for different response types
- 🧪 Type hints for better IDE support

## Installation

You can install the package using pip:

```bash
pip install stackspot-client
```

## Quick Start

```python
from stackspot_client import StackSpotConfig, StackSpotClient

# Configure the client
config = StackSpotConfig(
    base_url='https://genai-code-buddy-api.stackspot.com',
    auth_url='https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token',
    client_id='your_client_id',
    client_secret='your_client_secret'
)

# Create client instance
client = StackSpotClient(config)

# Execute a command
execution_id = client.execute_command('your_command', {'data': 'example'})

# Get the result
result = client.get_execution_result(execution_id)
print(result)
```

## Configuration

The `StackSpotConfig` class accepts the following parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| base_url | str | Yes | - | Base URL for the StackSpot API |
| client_id | str | Yes | - | Your StackSpot client ID |
| client_secret | str | Yes | - | Your StackSpot client secret |
| auth_url | str | No | https://idm.stackspot.com/stackspot-freemium/oidc/oauth/token | Authentication URL |
| max_retries | int | No | 30 | Maximum number of retries for result polling |
| retry_interval | int | No | 5 | Interval between retries in seconds |

## Usage Examples

### Knowledge Sources Management

```python
from stackspot_client import StackSpotConfig, StackSpotClient
from stackspot_client.knowledge_sources import KnowledgeSources

# Configure the client
config = StackSpotConfig(
    base_url='https://genai-code-buddy-api.stackspot.com',
    client_id='your_client_id',
    client_secret='your_client_secret'
)

# Create client instance
client = StackSpotClient(config)

# Create KnowledgeSources instance
ks = KnowledgeSources(client)

# Create a new knowledge source
response = ks.create_ks(
    slug="my-knowledge-source",
    name="My Knowledge Source",
    description="A knowledge source created via API",
    type="snippet"  # or "api" or "custom"
)

# Upload a file
file_upload_id = ks.upload_file(
    file_path="./document.md",
    ks_slug="my-knowledge-source"
)

# Upload content from a URL
upload_id = ks.upload_from_url(
    url="https://example.com/document",
    ks_slug="my-knowledge-source"
)

# Delete all files from a knowledge source
success = ks.delete_all_files("my-knowledge-source")
```

### Basic Command Execution

```python
from stackspot_client import StackSpotConfig, StackSpotClient

config = StackSpotConfig(
    base_url='https://genai-code-buddy-api.stackspot.com',
    client_id='your_client_id',
    client_secret='your_client_secret'
)

client = StackSpotClient(config)

# Execute a simple command
execution_id = client.execute_command('analyze-code', {
    'code': 'def hello(): print("Hello, World!")',
    'language': 'python'
})

# Get the result
result = client.get_execution_result(execution_id)
print(result)
```

### Error Handling

```python
from stackspot_client import StackSpotClient, StackSpotConfig, AuthenticationError, APIError

try:
    client = StackSpotClient(config)
    result = client.execute_command('invalid-command', {})
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except APIError as e:
    print(f"API error occurred: {e}")
```

## Response Format

The `get_execution_result` method returns a dictionary with the following structure:

```python
{
    'status': 'COMPLETED',  # or 'FAILED', 'RUNNING'
    'answer': '...',       # The actual response
    'progress': {          # Optional progress information
        'status': 'COMPLETE',
        'percentage': 100
    }
}
```

## Error Types

The library provides several error types for better error handling:

- `StackSpotError`: Base exception class
- `AuthenticationError`: Raised when authentication fails
- `APIError`: Raised when API calls fail

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support with the StackSpot API, please refer to the [official documentation](https://docs.stackspot.com).

## Changelog

### 0.1.2
- Added support for Knowledge Sources management
- Implemented knowledge source creation functionality
- Added support for file uploads
- Implemented URL content upload functionality
- Added functionality to delete all files from a knowledge source

### 0.1.0
- Initial release
- Basic authentication and command execution
- Result polling with retry mechanism
- Comprehensive error handling 