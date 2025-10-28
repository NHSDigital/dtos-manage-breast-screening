include scripts/shared.mk
include scripts/terraform/terraform.mk

.DEFAULT_GOAL := help

.PHONY: _clean-docker _install-poetry assets build clean config db dependencies deploy \
	diagrams githooks-config githooks-run help local migrate models personas rebuild-db run \
	seed seed-demo-data shell test test-end-to-end test-integration test-lint \
	test-lint-templates test-ui test-unit
.SILENT: help run

# ---------------------------------------------------------------------------
# Help & Meta
# ---------------------------------------------------------------------------
help: # Print help @Others
	printf "\nUsage: \033[3m\033[93m[arg1=val1] [arg2=val2] \033[0m\033[0m\033[32mmake\033[0m\033[34m <command>\033[0m\n\n"
	perl -e '$(HELP_SCRIPT)' $(MAKEFILE_LIST)

# ---------------------------------------------------------------------------
# Cleaning & Utility
# ---------------------------------------------------------------------------
clean:: _clean-docker  # Clean-up project resources (main) @Operations

_clean-docker:
	docker compose --env-file manage_breast_screening/config/.env down -v # remove the volume if it exists

diagrams:
	docker run -it --rm -p 8080:8080 -v ${PWD}/docs/diagrams:/usr/local/structurizr structurizr/lite

# ---------------------------------------------------------------------------
# Bootstrap & Environment
# ---------------------------------------------------------------------------
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
	poetry run playwright install

githooks-config:
	if ! command -v pre-commit >/dev/null 2>&1; then \
		pip install pre-commit; \
	fi
	pre-commit install

githooks-run: # Run git hooks configured in this repository @Operations
	pre-commit run \
		--config scripts/config/pre-commit.yaml \
		--all-files

_install-poetry:
	@if ! poetry --version >/dev/null 2>&1; then \
		echo "Installing poetry..."; \
		pip install poetry; \
	else \
		echo "poetry already installed"; \
	fi

manage_breast_screening/config/.env:
	cp manage_breast_screening/config/.env.tpl manage_breast_screening/config/.env

# ---------------------------------------------------------------------------
# Development Workflow
# ---------------------------------------------------------------------------
run: manage_breast_screening/config/.env # Start the development server @Development
	poetry run ./manage.py runserver

db: manage_breast_screening/config/.env # Start the development database @Development
	docker compose --env-file manage_breast_screening/config/.env up -d --wait

local: config seed-demo-data personas run

rebuild-db: _clean-docker db migrate seed-demo-data personas  # Create a fresh development database @Development

migrate:  # Run migrations
	poetry run ./manage.py migrate

personas: # Add personas to the database @Development
	poetry run ./manage.py create_personas

# run with ARGS="--noinput" to bypass confirmation prompt in CI etc
seed-demo-data:
	poetry run ./manage.py seed_demo_data $(ARGS)

models:
	poetry run ./manage.py shell -c "from django.apps import apps; print('\n'.join(f'{m._meta.app_label}.{m.__name__}' for m in apps.get_models()))"

shell:
	poetry run ./manage.py shell

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test: test-unit test-ui test-lint # Run all tests @Testing

test-unit: # Run unit tests @Testing
	poetry run pytest -m 'not system' --ignore manage_breast_screening/notifications/tests/dependencies --ignore manage_breast_screening/notifications/tests/integration --ignore manage_breast_screening/notifications/tests/end_to_end --cov --cov-report term-missing:skip-covered
	npm test -- --coverage

test-lint: # Lint files @Testing
	npm run lint
	poetry run ruff check manage_breast_screening
	poetry run python scripts/lint_model_usage_in_views.py

	# Enable this once we have fixed all the issues
	# make test-lint-templates

test-lint-templates: # Lint just the templates @Testing
	poetry run djlint -e jinja --lint --profile jinja manage_breast_screening

test-ui: # Run UI tests @Testing
	poetry run pytest manage_breast_screening/tests/system/general/test_user_views_clinic_show_page.py::TestUserViewsClinicShowPage::test_user_views_clinic_show_page --ignore manage_breast_screening/notifications

test-integration:
	cd manage_breast_screening/notifications && ./tests/integration/run.sh

test-end-to-end:
	cd manage_breast_screening/notifications && ./tests/end_to_end/run.sh

# ---------------------------------------------------------------------------
# Build & Deploy
# ---------------------------------------------------------------------------
build: # Build the project artefact @Pipeline
	docker build -t "app:$$(git rev-parse HEAD)" .

deploy: # Deploy the project artefact to the target environment @Pipeline
	# TODO: Implement the artefact deployment step
