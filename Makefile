

include scripts/shared.mk

clean:: _clean-docker  # Clean-up project resources (main) @Operations

# Configure development environment (main) @Configuration
config: manage_breast_screening/config/.env \
	_install-tools \
	_install-poetry \
	githooks-config \
	dependencies \
	assets \
	db migrate seed

dependencies: # Install dependencies needed to build and test the project @Pipeline
	poetry install
	npm install

assets: # Compile assets @Pipeline
	npm run compile

build: # Build the project artefact @Pipeline
	docker build -t "app:$$(git rev-parse HEAD)" .

deploy: # Deploy the project artefact to the target environment @Pipeline
	# TODO: Implement the artefact deployment step

githooks-config:
	if ! command -v pre-commit >/dev/null 2>&1; then \
		pip install pre-commit; \
	fi
	pre-commit install

githooks-run: # Run git hooks configured in this repository @Operations
	pre-commit run \
		--config scripts/config/pre-commit.yaml \
		--all-files

help: # Print help @Others
	printf "\nUsage: \033[3m\033[93m[arg1=val1] [arg2=val2] \033[0m\033[0m\033[32mmake\033[0m\033[34m <command>\033[0m\n\n"
	perl -e '$(HELP_SCRIPT)' $(MAKEFILE_LIST)

test: test-unit test-lint # Run all tests @Testing

test-unit: # Run unit tests @Testing
	poetry run pytest

test-lint: # Lint files @Testing
	# TODO

test-ui: # Run UI tests @Testing
	# TODO

run: manage_breast_screening/config/.env # Start the development server @Development
	poetry run ./manage.py runserver

db: manage_breast_screening/config/.env # Start the development database @Development
	docker compose --env-file manage_breast_screening/config/.env up -d --wait

rebuild-db: _clean-docker db migrate seed  # Create a fresh development database @Development

migrate:  # Run migrations
	poetry run ./manage.py migrate

seed:  # Load seed data
	poetry run ./manage.py loaddata clinics participants

_install-poetry:
	if ! command -v poetry >/dev/null 2>&1; then \
		pip install poetry; \
	else \
		echo "poetry already installed"; \
	fi

_clean-docker:
	docker compose --env-file manage_breast_screening/config/.env down -v # remove the volume if it exists

manage_breast_screening/config/.env:
	cp manage_breast_screening/config/.env.tpl manage_breast_screening/config/.env


.DEFAULT_GOAL := help
.PHONY: clean config dependencies build deploy githooks-config githooks-run help test test-unit test-lint test-ui run _install-poetry _clean-docker rebuild-db db migrate seed
.SILENT: help run
