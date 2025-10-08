import json
import time
import uuid

from flask import Flask, request
from jsonschema import ValidationError, validate

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return "OK"


@app.route("/token", methods=["POST"])
def token():
    return json.dumps({"access_token": "000111"}), 200


@app.route("/message/batch", methods=["POST"])
def message_batches():
    valid_headers, headers_error_message = verify_headers_for_consumers(
        dict(request.headers)
    )

    if not valid_headers:
        return json.dumps({"status": "failed", "error": headers_error_message}), 400

    json_data = request.json

    valid, message = validate_with_schema(json_data)

    if not valid:
        return json.dumps({"error": message}), 400

    messages = populate_message_ids(json_data["data"]["attributes"]["messages"])

    return json.dumps(
        {
            "data": {
                "type": "MessageBatch",
                "id": json_data["data"].get("id") or "2ZljUiS8NjJNs95PqiYOO7gAfJb",
                "attributes": {
                    "messageBatchReference": json_data["data"]["attributes"][
                        "messageBatchReference"
                    ],
                    "routingPlan": {
                        "id": "b838b13c-f98c-4def-93f0-515d4e4f4ee1",
                        "name": "Plan Abc",
                        "version": "ztoe2qRAM8M8vS0bqajhyEBcvXacrGPp",
                        "createdDate": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    },
                    "messages": messages,
                },
            }
        }
    ), 201


@app.route("/message/batch/recoverable-error", methods=["POST"])
def message_batch_with_error_response():
    return json.dumps(
        {
            "errors": [
                {
                    "id": "rrt-1931948104716186917-c-geu2-10664-3111479-3.0",
                    "code": "CM_TIMEOUT",
                    "links": {
                        "about": "https://digital.nhs.uk/developer/api-catalogue/nhs-notify"
                    },
                    "status": "408",
                    "title": "Request timeout",
                    "detail": "The service was unable to receive your request within the timeout period.",
                }
            ]
        }
    ), 408


@app.route("/message/batch/validation-error", methods=["POST"])
def message_batch_with_validation_error_response():
    return json.dumps(
        {
            "errors": [
                {
                    "id": "rrt-1931948104716186917-c-geu2-10664-3111479-3.0",
                    "code": "CM_INVALID_NHS_NUMBER",
                    "links": {
                        "about": "https://digital.nhs.uk/developer/api-catalogue/nhs-notify",
                        "nhsNumbers": "https://www.datadictionary.nhs.uk/attributes/nhs_number.html",
                    },
                    "status": "400",
                    "title": "Invalid nhs number",
                    "detail": "The value provided in this nhsNumber field is not a valid NHS number.",
                    "source": {
                        "pointer": "/data/attributes/messages/0/recipient/nhsNumber"
                    },
                }
            ]
        }
    ), 400


def validate_with_schema(data: dict):
    try:
        with open("schema.json") as file:
            schema = json.loads(file.read())
        subschema = schema["paths"]["/v1/message-batches"]["post"]["requestBody"][
            "content"
        ]["application/vnd.api+json"]["schema"]
        validate(instance=data, schema=subschema)
        return True, ""
    except ValidationError as e:
        return False, e.message
    except KeyError as e:
        return False, f"Invalid body: {e}"
    except Exception as e:
        return False, str(e)


def verify_headers_for_consumers(headers: dict) -> tuple[bool, str]:
    lc_headers = header_keys_to_lower(headers)
    if lc_headers.get("authorization") is None:
        return False, "Missing Authorization header"

    return True, ""


def header_keys_to_lower(headers: dict) -> dict:
    return {k.lower(): v for k, v in headers.items()}


def populate_message_ids(messages: list[dict]) -> list[dict]:
    for message in messages:
        message["id"] = uid(27) if not message.get("id") else message["id"]

    return messages


def uid(n) -> str:
    return uuid.uuid4().hex[0:n]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888)
