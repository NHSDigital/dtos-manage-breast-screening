import json
import os
from unittest.mock import patch

import pytest

from manage_breast_screening.batches.models import BatchPayload
from manage_breast_screening.batches.services import BatchService


class TestBatchService:
    @pytest.mark.django_db
    def test_create_batch_from_payload(self):
        fixture_path = (
            f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch.json"
        )
        with open(fixture_path) as f:
            batch_data_json = json.load(f)

        batch_data = BatchPayload.model_construct(**batch_data_json)

        batch = BatchService.create_batch_from_payload(batch_data)

        assert batch.bss_batch_id == batch_data.bssBatchID
        assert batch.bso_batch_id == batch_data.bsoBatchID
        assert json.loads(batch.batch_payload_json) == batch_data_json
        assert batch.created_at is not None
        assert batch.updated_at is not None

    @pytest.mark.django_db
    def test_create_batch_from_payload_database_error(self):
        fixture_path = (
            f"{os.path.dirname(os.path.realpath(__file__))}/fixtures/bss_batch.json"
        )
        with open(fixture_path) as f:
            batch_data_json = json.load(f)

        batch_data = BatchPayload.model_construct(**batch_data_json)

        with patch(
            "manage_breast_screening.batches.models.Batch.objects.create",
            side_effect=Exception("Database connection error"),
        ):
            with pytest.raises(Exception, match="Database connection error"):
                BatchService.create_batch_from_payload(batch_data)
