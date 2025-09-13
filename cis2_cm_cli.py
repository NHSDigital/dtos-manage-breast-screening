#!/usr/bin/env python3
"""
NHS CIS2 Connection Manager CLI Tool

A command-line interface for interacting with the NHS CIS2 Connection Manager API.
Supports authentication and configuration management operations.
"""

import getpass
import json
import sys
from typing import Any, Dict, List, Optional

import requests


class CIS2Client:
    """Client for interacting with the NHS CIS2 Connection Manager API."""

    BASE_URL = "https://connectionmanager.nhsint.auth-ptl.cis2.spineservices.nhs.uk"

    def __init__(self):
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.team_id: Optional[str] = None
        self.secret: Optional[str] = None

    def authenticate(self, secret: str) -> Dict[str, Any]:
        """Authenticate with the API using the provided secret."""
        url = f"{self.BASE_URL}/api/auth"
        headers = {
            "Authorization": f"SecretAuth {secret}",
            "Content-Type": "application/json",
        }

        try:
            response = self.session.post(url, headers=headers)
            response.raise_for_status()

            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            self.secret = secret

            # Update session headers with access token
            if self.access_token:
                self.session.headers.update(
                    {"Authorization": f"Bearer {self.access_token}"}
                )

            return auth_data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Authentication failed: {e}")

    def get_configs(self, team_id: str) -> Dict[str, Any]:
        """Get list of configs for the specified team."""
        url = f"{self.BASE_URL}/api/configs/{team_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get configs: {e}")

    def get_config(self, team_id: str, config_id: str) -> Dict[str, Any]:
        """Get a specific config by ID for the specified team."""
        url = f"{self.BASE_URL}/api/configs/{team_id}/{config_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get config: {e}")

    def create_config(
        self, team_id: str, client_name: str, redirect_uris: List[str]
    ) -> Dict[str, Any]:
        """Create a new config for the specified team."""
        url = f"{self.BASE_URL}/api/configs/{team_id}"

        payload = {"client_name": client_name, "redirect_uris": redirect_uris}

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # For HTTP errors, try to get detailed error information from response
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    raise Exception(
                        f"Failed to create config (HTTP {e.response.status_code}): {json.dumps(error_detail, indent=2)}"
                    )
                except (ValueError, json.JSONDecodeError):
                    # If response isn't JSON, show the raw text
                    raise Exception(
                        f"Failed to create config (HTTP {e.response.status_code}): {e.response.text}"
                    )
            else:
                raise Exception(f"Failed to create config: {e}")

    def create_config_advanced(
        self, team_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new config with full payload support."""
        url = f"{self.BASE_URL}/api/configs/{team_id}"

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # For HTTP errors, try to get detailed error information from response
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    raise Exception(
                        f"Failed to create config (HTTP {e.response.status_code}): {json.dumps(error_detail, indent=2)}"
                    )
                except (ValueError, json.JSONDecodeError):
                    # If response isn't JSON, show the raw text
                    raise Exception(
                        f"Failed to create config (HTTP {e.response.status_code}): {e.response.text}"
                    )
            else:
                raise Exception(f"Failed to create config: {e}")

    def update_config(
        self,
        team_id: str,
        config_id: str,
        client_config: Dict[str, Any],
        config_hash: str,
    ) -> Dict[str, Any]:
        """Update an existing config for the specified team."""
        url = f"{self.BASE_URL}/api/configs/{team_id}/{config_id}"

        # Add hash as query parameter
        params = {"hash": config_hash}

        try:
            response = self.session.put(url, params=params, json=client_config)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # For HTTP errors, try to get detailed error information from response
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    raise Exception(
                        f"Failed to update config (HTTP {e.response.status_code}): {json.dumps(error_detail, indent=2)}"
                    )
                except (ValueError, json.JSONDecodeError):
                    # If response isn't JSON, show the raw text
                    raise Exception(
                        f"Failed to update config (HTTP {e.response.status_code}): {e.response.text}"
                    )
            else:
                raise Exception(f"Failed to update config: {e}")


class CIS2CLI:
    """Command-line interface for the CIS2 Connection Manager."""

    # ANSI color codes
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    def __init__(self):
        self.client = CIS2Client()
        self.authenticated = False
        self.last_config_hash: Optional[str] = None
        self.last_config_id: Optional[str] = None

    def setup_credentials(self):
        """Prompt user for secret and team ID, then authenticate."""

        print(f"""
{self.BLUE}    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║{self.WHITE}    ███    ██ ██   ██ ███████     ██████ ██ ███████ ██████{self.BLUE}     ║
    ║{self.WHITE}    ████   ██ ██   ██ ██         ██      ██ ██           ██{self.BLUE}    ║
    ║{self.WHITE}    ██ ██  ██ ███████ ███████    ██      ██ ███████  █████{self.BLUE}     ║
    ║{self.WHITE}    ██  ██ ██ ██   ██      ██    ██      ██      ██ ██{self.BLUE}         ║
    ║{self.WHITE}    ██   ████ ██   ██ ███████     ██████ ██ ███████ ███████{self.BLUE}    ║
    ║                                                               ║
    ║{self.WHITE}                Connection Manager CLI Tool                    {self.BLUE}║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝{self.RESET}
        """)
        print("=" * 40)

        # Get secret
        secret = getpass.getpass("Enter your API secret: ")
        if not secret:
            print("Error: Secret is required")
            sys.exit(1)

        # Authenticate
        try:
            print("Authenticating...")
            auth_result = self.client.authenticate(secret)
            print(f"{self.GREEN}✓ Authentication successful{self.RESET}")

            self.authenticated = True

            # Handle team ID selection
            if "team_ids" not in auth_result or not auth_result["team_ids"]:
                print("✗ Error: No team IDs available for this account")
                print(
                    "Please contact your administrator to ensure your account has team access."
                )
                sys.exit(1)

            team_ids = auth_result["team_ids"]

            print("\nAvailable team IDs:")
            for i, team_id in enumerate(team_ids, 1):
                print(f"{i}. {team_id}")

            while True:
                try:
                    choice = input(f"Select team ID (1-{len(team_ids)}): ").strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(team_ids):
                        selected_team_id = team_ids[choice_num - 1]
                        self.client.team_id = selected_team_id
                        print(
                            f"{self.GREEN}✓ Team ID set to: {selected_team_id}{self.RESET}"
                        )
                        break
                    else:
                        print(
                            f"Invalid choice. Please enter a number between 1 and {len(team_ids)}."
                        )
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\nOperation cancelled.")
                    sys.exit(1)

        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            sys.exit(1)

        print()

    def show_menu(self):
        """Display the main menu options."""
        print("Available options:")
        print("1. List configurations")
        print("2. Display specific configuration")
        print("3. Create new configuration")
        print("4. Update existing configuration")
        print("5. Re-authenticate")
        print("6. Change team ID")
        print("7. Quit")
        print()

    def list_configs(self):
        """List all configurations for the current team."""
        try:
            print(f"Fetching configurations for team: {self.client.team_id}")
            configs = self.client.get_configs(self.client.team_id)

            print("\nConfigurations:")
            print("-" * 20)
            if isinstance(configs, dict) and "configs" in configs:
                for config in configs["configs"]:
                    print(f"• {config}")
            elif isinstance(configs, list):
                for config in configs:
                    print(f"• {config}")
            else:
                print(json.dumps(configs, indent=2))

        except Exception as e:
            print(f"✗ Error listing configs: {e}")

    def display_config(self):
        """Display details of a specific configuration."""
        try:
            # First, get the list of available configurations
            print(f"Fetching configurations for team: {self.client.team_id}")
            configs_response = self.client.get_configs(self.client.team_id)

            # Extract config IDs from the response
            config_ids = []
            if isinstance(configs_response, dict) and "configs" in configs_response:
                config_ids = configs_response["configs"]
            elif isinstance(configs_response, list):
                config_ids = configs_response
            else:
                print("✗ Error: Unexpected configuration list format")
                print(json.dumps(configs_response, indent=2))
                return

            if not config_ids:
                print("✗ Error: No configurations available for this team")
                return

            # Show numbered menu for selection
            print("\nAvailable configurations:")
            for i, config_id in enumerate(config_ids, 1):
                print(f"{i}. {config_id}")

            while True:
                try:
                    choice = input(
                        f"Select configuration (1-{len(config_ids)}): "
                    ).strip()
                    choice_num = int(choice)

                    if 1 <= choice_num <= len(config_ids):
                        selected_config_id = config_ids[choice_num - 1]
                        break
                    else:
                        print(
                            f"Invalid choice. Please enter a number between 1 and {len(config_ids)}."
                        )
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    print("\nOperation cancelled.")
                    return

            # Fetch and display the selected configuration
            print(f"Fetching configuration '{selected_config_id}'...")
            config = self.client.get_config(self.client.team_id, selected_config_id)

            # Store config hash and ID for future updates
            if isinstance(config, dict) and "hash" in config:
                self.last_config_hash = config["hash"]
                self.last_config_id = selected_config_id
                print(
                    f"{self.GREEN}✓ Config hash cached for updates: {self.last_config_hash[:8]}...{self.RESET}"
                )

            print(f"\nConfiguration Details for '{selected_config_id}':")
            print("=" * 40)
            print(json.dumps(config, indent=2))

        except Exception as e:
            print(f"✗ Error displaying config: {e}")

    def create_config(self):
        """Create a new configuration."""
        try:
            print("Create new configuration")
            print("-" * 25)

            client_name = input("Enter client name: ").strip()
            if not client_name:
                print("Error: Client name is required")
                return

            redirect_uris_input = input(
                "Enter redirect URIs (comma-separated): "
            ).strip()
            if not redirect_uris_input:
                print("Error: At least one redirect URI is required")
                return

            redirect_uris = [uri.strip() for uri in redirect_uris_input.split(",")]

            # Get optional fields
            description = input("Enter description (optional): ").strip() or None

            backchannel_logout_uri = (
                input("Enter backchannel logout URI (optional): ").strip() or None
            )

            print("\nAuthentication method:")
            print("1. client_secret_basic (default)")
            print("2. private_key_jwt")
            auth_choice = (
                input("Choose authentication method (1-2, default 1): ").strip() or "1"
            )

            token_endpoint_auth_method = "client_secret_basic"
            jwks_uri = None
            jwks_uri_signing_algorithm = None

            if auth_choice == "2":
                token_endpoint_auth_method = "private_key_jwt"
                jwks_uri = input(
                    "Enter JWKS URI (required for private_key_jwt): "
                ).strip()
                if not jwks_uri:
                    print("Error: JWKS URI is required when using private_key_jwt")
                    return

                jwks_uri_signing_algorithm = (
                    input("Enter JWKS URI signing algorithm (e.g., RS512): ").strip()
                    or None
                )

            # Build payload with only non-None values
            payload = {
                "client_name": client_name,
                "redirect_uris": redirect_uris,
                "token_endpoint_auth_method": token_endpoint_auth_method,
            }

            if description:
                payload["description"] = description
            if backchannel_logout_uri:
                payload["backchannel_logout_uri"] = backchannel_logout_uri
            if jwks_uri:
                payload["jwks_uri"] = jwks_uri
            if jwks_uri_signing_algorithm:
                payload["jwks_uri_signing_algorithm"] = jwks_uri_signing_algorithm

            print(f"Creating config for team: {self.client.team_id}")
            print("Payload being sent:")
            print(json.dumps(payload, indent=2))
            print()

            result = self.client.create_config_advanced(self.client.team_id, payload)

            print(f"{self.GREEN}✓ Configuration created successfully{self.RESET}")
            print(json.dumps(result, indent=2))

        except Exception as e:
            print(f"✗ Error creating config: {e}")

    def update_config(self):
        """Update an existing configuration."""
        # Check if we have a cached hash from displaying a config
        if not self.last_config_hash or not self.last_config_id:
            print("Error: No config hash available for update.")
            print("Please display a configuration first to cache its hash.")
            return

        try:
            print("Update existing configuration")
            print("-" * 30)
            print(f"Config ID: {self.last_config_id}")
            print(f"Using hash: {self.last_config_hash[:8]}...")
            print()

            print("Enter the new client_config as JSON:")
            print(
                "(You can paste a multi-line JSON object. Press Enter on an empty line when done)"
            )

            json_lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                json_lines.append(line)

            if not json_lines:
                print("Error: JSON payload is required")
                return

            json_text = "\n".join(json_lines)

            # Parse the JSON to validate it
            try:
                client_config = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON format - {e}")
                return

            print(
                f"Updating config '{self.last_config_id}' for team: {self.client.team_id}"
            )
            print("Payload being sent:")
            print(f"  client_config: {json.dumps(client_config, indent=4)}")
            print(f"  hash: {self.last_config_hash}")
            print()

            result = self.client.update_config(
                self.client.team_id,
                self.last_config_id,
                client_config,
                self.last_config_hash,
            )

            print(f"{self.GREEN}✓ Configuration updated successfully{self.RESET}")
            print(json.dumps(result, indent=2))

            # Update the cached hash if provided in response
            if isinstance(result, dict) and "hash" in result:
                self.last_config_hash = result["hash"]
                print(
                    f"{self.GREEN}✓ New hash cached: {self.last_config_hash[:8]}...{self.RESET}"
                )

        except Exception as e:
            print(f"✗ Error updating config: {e}")

    def re_authenticate(self):
        """Re-authenticate with a new secret."""
        secret = getpass.getpass("Enter your API secret: ")
        if not secret:
            print("Error: Secret is required")
            return

        try:
            print("Re-authenticating...")
            self.client.authenticate(secret)
            print(f"{self.GREEN}✓ Re-authentication successful{self.RESET}")
            self.authenticated = True
        except Exception as e:
            print(f"✗ Re-authentication failed: {e}")
            self.authenticated = False

    def change_team_id(self):
        """Change the current team ID."""
        team_id = input("Enter new team ID: ").strip()
        if not team_id:
            print("Error: Team ID is required")
            return

        self.client.team_id = team_id
        print(f"{self.GREEN}✓ Team ID changed to: {team_id}{self.RESET}")

    def run(self):
        """Run the CLI application."""
        # Initial setup
        self.setup_credentials()

        # Main loop
        while True:
            self.show_menu()

            try:
                choice = input("Enter your choice (1-7): ").strip()
                print()

                if choice == "1":
                    self.list_configs()
                elif choice == "2":
                    self.display_config()
                elif choice == "3":
                    self.create_config()
                elif choice == "4":
                    self.update_config()
                elif choice == "5":
                    self.re_authenticate()
                elif choice == "6":
                    self.change_team_id()
                elif choice == "7":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1-7.")

                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")


if __name__ == "__main__":
    cli = CIS2CLI()
    cli.run()
