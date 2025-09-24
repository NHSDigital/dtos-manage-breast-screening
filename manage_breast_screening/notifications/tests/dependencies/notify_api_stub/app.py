import json
import time
import uuid

import requests
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
        return json.dumps({"error": message}), 422

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


def validate_with_schema(data: dict):
    try:
        schema = requests.get("https://digital.nhs.uk/restapi/oas/540802").json()
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
