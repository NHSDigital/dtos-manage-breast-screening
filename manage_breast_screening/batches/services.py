from django.db import transaction

from .models import Batch, BatchPayload


class BatchService:
    """Service for handling batch operations."""

    @transaction.atomic
    @staticmethod
    def create_batch_from_payload(payload: BatchPayload) -> Batch:
        batch = Batch.objects.create(
            bss_batch_id=payload.bssBatchID,
            bso_batch_id=payload.bsoBatchID,
            batch_payload_json=payload.model_dump_json(),
        )

        return batch
