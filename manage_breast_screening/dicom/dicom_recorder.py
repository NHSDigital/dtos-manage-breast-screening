import io
import logging
from datetime import datetime

import numpy as np
import pydicom
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image as PILImage

from .models import Image, Series, Study

logger = logging.getLogger(__name__)


class DicomRecorder:
    @staticmethod
    def get_or_create_records(
        source_message_id: str, dicom_file: bytes
    ) -> tuple[Study, Series, Image]:
        ds = pydicom.dcmread(dicom_file)
        study_uid = ds.StudyInstanceUID
        series_uid = ds.SeriesInstanceUID
        sop_uid = ds.SOPInstanceUID

        logger.info(
            f"Processing DICOM file with StudyInstanceUID={study_uid}, "
            f"SeriesInstanceUID={series_uid}, SOPInstanceUID={sop_uid}, "
            f"PatientID={getattr(ds, 'PatientID', '')}, "
        )

        study, _ = Study.objects.get_or_create(
            study_instance_uid=study_uid,
            source_message_id=source_message_id,
            defaults={
                "patient_id": getattr(ds, "PatientID", ""),
                "date_and_time": __class__.study_date_and_time(ds),
                "description": getattr(ds, "StudyDescription", ""),
            },
        )

        series, _ = Series.objects.get_or_create(
            series_instance_uid=series_uid,
            study=study,
            defaults={
                "modality": getattr(ds, "Modality", ""),
                "series_number": getattr(ds, "SeriesNumber", None),
            },
        )

        image, created = Image.objects.get_or_create(
            sop_instance_uid=sop_uid,
            series=series,
            defaults={
                "instance_number": getattr(ds, "InstanceNumber", None),
                "laterality": getattr(ds, "ImageLaterality", ""),
                "view_position": getattr(ds, "ViewPosition", ""),
            },
        )
        if created:
            image.dicom_file.save(f"{sop_uid}.dcm", dicom_file)
            image.image_file.save(
                f"{sop_uid}.jpeg", __class__.dataset_to_jpeg(sop_uid, ds)
            )

        return study, series, image

    @staticmethod
    def study_date_and_time(ds) -> datetime | None:
        study_date = getattr(ds, "StudyDate", "")
        study_time = getattr(ds, "StudyTime", "")
        if study_date and study_time:
            return datetime.strptime(
                study_date + study_time.split(".")[0], "%Y%m%d%H%M%S"
            )
        return None

    @staticmethod
    def dataset_to_jpeg(sop_uid: str, ds: pydicom.Dataset) -> InMemoryUploadedFile:
        """Convert a DICOM dataset to a JPEG image and return it as an InMemoryUploadedFile."""
        # Normalize pixel data to 0-255 and convert to uint8
        pixel_array = ds.pixel_array
        pixel_array = pixel_array.astype(np.float32)

        if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
            pixel_array = np.max(pixel_array) - pixel_array

        pixel_array -= pixel_array.min()
        pixel_array /= pixel_array.max()
        pixel_array *= 255.0
        pixel_array = pixel_array.astype(np.uint8)
        # Create a PIL image from the pixel array
        image = PILImage.fromarray(pixel_array, mode="L")
        in_memory_file = io.BytesIO()
        image.save(in_memory_file, format="JPEG")

        return InMemoryUploadedFile(
            in_memory_file,
            name=f"{sop_uid}.jpeg",
            field_name="file",
            content_type="image/jpeg",
            size=in_memory_file.getbuffer().nbytes,
            charset=None,
        )
