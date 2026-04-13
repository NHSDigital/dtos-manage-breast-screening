import tempfile
import uuid
from datetime import datetime
from unittest.mock import patch

import numpy as np
import pydicom
import pytest

from manage_breast_screening.dicom.dicom_recorder import (
    DicomProcessingError,
    DicomRecorder,
)
from manage_breast_screening.dicom.models import Image, Series, Study
from manage_breast_screening.gateway.tests.factories import GatewayActionFactory
from manage_breast_screening.participants.models.appointment import (
    AppointmentStatusNames,
)
from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestDicomRecorder:
    @pytest.fixture
    def gateway_action(self, source_message_id):
        return GatewayActionFactory(
            id=source_message_id,
            appointment=AppointmentFactory(
                current_status=AppointmentStatusNames.IN_PROGRESS
            ),
        )

    @pytest.fixture
    def source_message_id(self):
        return str(uuid.uuid4())

    def test_get_or_create_records(self, source_message_id, dataset, gateway_action):
        """
        Test that when a valid DICOM file is processed, the correct Study, Series, and Image records
        are created with the expected attributes, and that the DICOM and JPEG files are stored correctly.
        """
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
        assert image.laterality == dataset.ImageLaterality
        assert image.view_position == dataset.ViewPosition

        assert image.dicom_file.name.endswith(f"{dataset.SOPInstanceUID}.dcm")
        assert image.dicom_file.size > 0
        assert image.dicom_file.storage.exists(image.dicom_file.name)

        assert image.image_file.name.endswith(f"{dataset.SOPInstanceUID}.jpeg")
        assert image.image_file.size > 0
        assert image.image_file.storage.exists(image.image_file.name)

    def test_get_or_create_records_duplicate(
        self, source_message_id, dataset, gateway_action
    ):
        """
        Test that if a DICOM file with the same SOPInstanceUID is processed again,
        it returns the existing records instead of creating new ones.
        """
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

    def test_get_or_create_records_invalid_laterality_and_view_position(
        self, source_message_id, dataset, gateway_action
    ):
        """
        Test that if a series already has an image with a certain laterality and view position,
        then adding another image with a different laterality and view position raises an error.
        """
        dataset.ImageLaterality = "L"
        dataset.ViewPosition = "CC"

        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                DicomRecorder.get_or_create_records(source_message_id, dicom_file)

        dataset.ViewPosition = "MLO"

        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                with pytest.raises(DicomProcessingError):
                    DicomRecorder.get_or_create_records(source_message_id, dicom_file)

    def test_get_or_create_records_invalid_dicom(
        self, source_message_id, gateway_action
    ):
        """
        Test that if the DICOM file is invalid (e.g. missing required attributes), it raises an error.
        """
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

    def test_get_or_create_records_appointment_not_in_progress(
        self, source_message_id, dataset
    ):
        """
        Test that if the associated appointment is not in progress, it raises an error.
        """
        GatewayActionFactory(
            id=source_message_id,
            appointment=AppointmentFactory(
                current_status=AppointmentStatusNames.SCREENED
            ),
        )
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                with pytest.raises(DicomProcessingError):
                    DicomRecorder.get_or_create_records(source_message_id, dicom_file)

    @pytest.mark.parametrize(
        "cs_value, expected",
        [
            ("YES", True),
            ("NO", False),
            ("UNKNOWN", False),
            ("", False),
        ],
    )
    def test_get_or_create_implant_presence(
        self, source_message_id, dataset, gateway_action, cs_value, expected
    ):
        """
        Test that the BreastImplantPresent attribute is correctly interpreted as a boolean value.
        """
        dataset.add_new("BreastImplantPresent", "CS", cs_value)
        with tempfile.NamedTemporaryFile() as temp_file:
            pydicom.filewriter.dcmwrite(
                temp_file.name, dataset, write_like_original=False
            )
            with open(temp_file.name, "rb") as dicom_file:
                _, _, image = DicomRecorder.get_or_create_records(
                    source_message_id, dicom_file
                )

        assert image.implant_present is expected


class TestJpegConversion:
    def test_dataset_to_jpeg(self, dataset):
        expected_pixel_array = self.expected_pixel_array(dataset)

        with patch(f"{DicomRecorder.__module__}.PILImage.fromarray") as mock_fromarray:
            DicomRecorder.dataset_to_jpeg(dataset.SOPInstanceUID, dataset)

            assert mock_fromarray.call_count == 1
            assert mock_fromarray.call_args[0][0].shape == expected_pixel_array.shape
            assert np.array_equal(mock_fromarray.call_args[0][0], expected_pixel_array)
            assert mock_fromarray.call_args[1]["mode"] == "L"

    def test_dataset_to_jpeg_monochrome1(self, dataset):
        expected_pixel_array = self.expected_pixel_array(dataset)

        with patch(f"{DicomRecorder.__module__}.PILImage.fromarray") as mock_fromarray:
            DicomRecorder.dataset_to_jpeg(dataset.SOPInstanceUID, dataset)

            assert mock_fromarray.call_args[0][0].shape == expected_pixel_array.shape
            assert np.array_equal(mock_fromarray.call_args[0][0], expected_pixel_array)

    def expected_pixel_array(self, dataset):
        pixel_array = dataset.pixel_array.astype(np.float32)
        if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
            pixel_array = np.max(pixel_array) - pixel_array
        pixel_array -= pixel_array.min()
        pixel_array /= pixel_array.max()
        pixel_array *= 255.0
        return pixel_array.astype(np.uint8)
