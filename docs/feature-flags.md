# Feature flags

Feature flags are implemented using [OpenFeature](https://openfeature.dev/) with an `InMemoryProvider`. Flags are declared in YAML files and loaded at startup.

## Flag files

Each environment has its own flag file. The application selects the file based on the `DEPLOYED_TO` environment variable, falling back to `flags.yml` for local development where `DEPLOYED_TO` is not set.

| Environment                  | File                   |
| ---------------------------- | ---------------------- |
| dev                          | `flags.dev.yml`        |
| review                       | `flags.review.yml`     |
| preprod                      | `flags.preprod.yml`    |
| production                   | `flags.production.yml` |
| local (no `DEPLOYED_TO` set) | `flags.yml`            |

## Adding a flag

**1. Declare the flag in each environment's file.**

Add an entry to all five flag files (`flags.yml`, `flags.dev.yml`, `flags.review.yml`, `flags.preprod.yml`, `flags.production.yml`). Set the value to `true` to enable or `false` to disable in that environment.

```yaml
flags:
  my_flag: false
```

**2. Check the flag in application code.**

```python
from openfeature import api

client = api.get_client()
if client.get_boolean_value("my_flag", False):
    # feature is enabled
```

The second argument to `get_boolean_value` is the fallback returned if the flag is missing or the provider is unavailable. If a flag name is not found in the YAML file, OpenFeature silently returns the fallback rather than raising an error — so a typo in a flag name will return `False` without any indication something is wrong.

## Enabling a flag in tests

Use the `with_flag_enabled` fixture to turn a flag on for the duration of a single test:

```python
def test_something(with_flag_enabled):
    with_flag_enabled("my_flag")
    # flag is enabled for this test only
```

Multiple flags can be enabled by calling it more than once:

```python
def test_something(with_flag_enabled):
    with_flag_enabled("my_flag")
    with_flag_enabled("another_flag")
```

In class-based tests the fixture must be relayed via an `autouse` fixture so it is accessible to helper methods:

```python
@pytest.fixture(autouse=True)
def flags(self, with_flag_enabled):
    self.with_flag_enabled = with_flag_enabled

def and_my_flag_is_enabled(self):
    self.with_flag_enabled("my_flag")
```

After each test the flags are reset to the defaults from the YAML file.
