import tempfile
from unittest.mock import patch

import pydicom
import pytest

from manage_breast_screening.dicom.dicom_recorder import DicomRecorder
from manage_breast_screening.dicom.models import Image, Series, Study


class TestDicomRecorder:
    @pytest.fixture
    def source_message_id(self):
        return "test-source-message-id"

    @pytest.mark.django_db
    def test_create_records(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                records = DicomRecorder.create_records(source_message_id, dicom_file)

        assert records is not None
        study, series, image = records
        assert isinstance(study, Study)
        assert isinstance(series, Series)
        assert isinstance(image, Image)
        assert study.study_instance_uid == dataset.StudyInstanceUID
        assert study.source_message_id == source_message_id
        assert series.series_instance_uid == dataset.SeriesInstanceUID
        assert image.sop_instance_uid == dataset.SOPInstanceUID
        assert study.patient_id == dataset.PatientID
        assert study.date == dataset.StudyDate
        assert study.time == dataset.StudyTime
        assert study.description == dataset.StudyDescription
        assert series.modality == dataset.Modality
        assert series.series_number == dataset.SeriesNumber
        assert image.instance_number == dataset.InstanceNumber

    @pytest.mark.django_db
    def test_create_records_duplicate(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                DicomRecorder.create_records(source_message_id, dicom_file)

            with open(temp_file.name, "rb") as dicom_file:
                assert (
                    DicomRecorder.create_records(source_message_id, dicom_file) is None
                )

    @pytest.mark.django_db
    def test_create_records_invalid_dicom(self, source_message_id):
        with tempfile.NamedTemporaryFile() as temp_file:
            invalid_ds = pydicom.Dataset()
            invalid_ds.transfer_syntax_uid = pydicom.uid.ExplicitVRLittleEndian
            invalid_file_meta = pydicom.Dataset()
            invalid_file_meta.TransferSyntaxUID = invalid_ds.transfer_syntax_uid
            invalid_file_meta.MediaStorageSOPClassUID = pydicom.uid.generate_uid()
            invalid_file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
            invalid_ds.file_meta = invalid_file_meta

            pydicom.filewriter.dcmwrite(
                temp_file.name, invalid_ds, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                with pytest.raises(AttributeError):
                    DicomRecorder.create_records(source_message_id, dicom_file)

    @pytest.mark.django_db
    def test_create_records_transaction_rollback(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with patch.object(Image, "save", side_effect=Exception("Noooo!")):
                with open(temp_file.name, "rb") as dicom_file:
                    with pytest.raises(Exception):
                        DicomRecorder.create_records(source_message_id, dicom_file)

            assert Study.objects.count() == 0
            assert Series.objects.count() == 0
            assert Image.objects.count() == 0
