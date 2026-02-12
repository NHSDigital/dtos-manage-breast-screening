# Manage Breast Screening Gateway application

Manage communicates with Gateway applications deployed within NHS Trust networks.
The Django Gateway application defined in this directory contains models and services required to configure connections to multiple Gateways, and to send worklist data to the Gateways.

## Configuration

Communication uses Azure Relay which relies on websockets.

The `Relay` model defines the connection details for a Gateway. A shared access key should be stored in Azure Key Vault and the `shared_access_key_variable_name` field should be set to the name of the ENV var referencing the secret. (Note that keyvault secrets are hyphen delimited, but ENV vars are underscore delimited).
The `RelayURI` utility class provides a method to generate the URI with appropriate SAS Token for the Azure Relay connection based on the `Relay` model instance.
The `RelayService` class provides methods to send worklist data to the configured Gateways and to act on acknowledgement or exceptions.

The `WorklistItemService` class provides a method to create a `GatewayAction` instance with the appropriate payload for an appointment.

## Usage

### 1. Create a Relay instance to define the connection details for the Gateway.

```python
# A Relay instance is required to make the connection to the Gateway.
relay = Relay(
    name='Example Relay',
    namespace='example-namespace',
    entity_name='example-entity',
    shared_access_key_variable_name='EXAMPLE_RELAY_KEY'
    provider=Provider.objects.get(name='Example Provider')
)
relay.save()
```

### 2. Create a GatewayAction for an appointment.

```python
appointment = Appointment.objects.get(id=1)

action = WorklistItemService.create(appointment)
```

### 3. Send the action payload to the Gateway using the RelayService.

```python
# Send the action payload to the Gateway using the RelayService.
RelayService.send_worklist_data(relay, action)
```
