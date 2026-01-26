import tempfile
from datetime import datetime

import pydicom
import pytest

from manage_breast_screening.dicom.dicom_recorder import DicomRecorder
from manage_breast_screening.dicom.models import Image, Series, Study


class TestDicomRecorder:
    @pytest.fixture
    def source_message_id(self):
        return "test-source-message-id"

    @pytest.mark.django_db
    def test_get_or_create_records(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                records = DicomRecorder.get_or_create_records(
                    source_message_id, dicom_file
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
        assert study.date_and_time == datetime(2024, 1, 1, 12, 0, 0)
        assert study.description == dataset.StudyDescription
        assert series.modality == dataset.Modality
        assert series.series_number == dataset.SeriesNumber
        assert image.instance_number == dataset.InstanceNumber

        assert image.dicom_file.name.endswith(f"{dataset.SOPInstanceUID}.dcm")
        assert image.dicom_file.size > 0
        assert image.dicom_file.storage.exists(image.dicom_file.name)

        assert image.image_file.name.endswith(f"{dataset.SOPInstanceUID}.jpeg")
        assert image.image_file.size > 0
        assert image.image_file.storage.exists(image.image_file.name)

    @pytest.mark.django_db
    def test_get_or_create_records_duplicate(self, source_message_id, dataset):
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                study, series, image = DicomRecorder.get_or_create_records(
                    source_message_id, dicom_file
                )

            with open(temp_file.name, "rb") as dicom_file:
                assert DicomRecorder.get_or_create_records(
                    source_message_id, dicom_file
                ) == (
                    study,
                    series,
                    image,
                )

    def test_get_or_create_records_invalid_dicom(self, source_message_id):
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
                    DicomRecorder.get_or_create_records(source_message_id, dicom_file)
