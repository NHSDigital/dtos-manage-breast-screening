FROM python:3.13

COPY --from=root_dir pyproject.toml /
COPY --from=root_dir poetry.lock /

COPY --from=root_dir manage_breast_screening/notifications/tests/integration/runner/test_api_client_can_call_cmapi.py manage_breast_screening/notifications/tests/integration/test_api_client_can_call_cmapi.py
COPY --from=root_dir manage_breast_screening/notifications/api_client.py manage_breast_screening/notifications/api_client.py
COPY --from=root_dir manage_breast_screening/notifications/tests/factories.py manage_breast_screening/notifications/factories.py
COPY --from=root_dir manage_breast_screening/notifications/models.py manage_breast_screening/notifications/models.py
COPY --from=root_dir manage_breast_screening/__init__.py manage_breast_screening/__init__.py
COPY --from=root_dir manage_breast_screening/notifications/__init__.py manage_breast_screening/notifications/__init__.
COPY --from=root_dir manage_breast_screening/notifications/tests/__init__.py manage_breast_screening/notifications/tests/__init__.py
COPY --from=root_dir manage_breast_screening/notifications/tests/integration/__init__.py manage_breast_screening/notifications/tests/integration/__init__.py

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry remove pytest-django
RUN poetry install