import uuid
from typing import List

from django.db import models
from ninja import Schema

from ..core.models import BaseModel


class BatchRecord(Schema):
    nhsNumber: str
    familyName: str
    givenNames: str
    birthDate: str
    callRecallStatus: str
    namePrefix: str
    addressLine1: str
    addressLine2: str
    addressLine3: str
    addressLine4: str
    addressLine5: str
    postcode: str
    gpPracticeCode: str
    gpPracticeName: str
    prevActualScreeningDate: str
    category: str
    lastEpisodeType: str


class BatchPayload(Schema):
    linkCode: str
    bssBatchID: str
    bsoBatchID: str
    totalSubjectsInBatch: str
    selectDate: str
    totalNormalCall: str
    totalNormalRecall: str
    transferDate: str
    transferTime: str
    records: List[BatchRecord]


class Batch(BaseModel):
    """
    Stores batches from BS Select that have been received but not yet processed.
    """

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    bss_batch_id = models.CharField(max_length=255, null=False, unique=True)
    bso_batch_id = models.CharField(max_length=255, null=False)
    batch_payload_json = models.JSONField(null=False)

    class Meta:
        verbose_name_plural = "Unprocessed batches"
