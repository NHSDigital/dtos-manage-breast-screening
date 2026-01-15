import tempfile

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
                records = DicomRecorder.create_records(
                    source_message_id, dataset, dicom_file
                )

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
                DicomRecorder.create_records(source_message_id, dataset, dicom_file)

        assert (
            DicomRecorder.create_records(source_message_id, dataset, dicom_file) is None
        )

    def test_create_records_invalid_dicom(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            invalid_ds = pydicom.Dataset()
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                with pytest.raises(AttributeError):
                    DicomRecorder.create_records(
                        source_message_id, invalid_ds, dicom_file
                    )
