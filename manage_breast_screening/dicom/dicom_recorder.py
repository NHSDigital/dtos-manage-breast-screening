from datetime import datetime

import pydicom

from .models import Image, Series, Study


class DicomRecorder:
    @staticmethod
    def get_or_create_records(
        source_message_id: str, dicom_file: bytes
    ) -> tuple[Study, Series, Image]:
        ds = pydicom.dcmread(dicom_file)
        study_uid = ds.StudyInstanceUID
        series_uid = ds.SeriesInstanceUID
        sop_uid = ds.SOPInstanceUID

        study, _ = Study.objects.get_or_create(
            study_instance_uid=study_uid,
            defaults={
                "patient_id": getattr(ds, "PatientID", ""),
                "date_and_time": __class__.study_date_and_time(ds),
                "description": getattr(ds, "StudyDescription", ""),
                "source_message_id": source_message_id,
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
            },
        )
        if created:
            image.dicom_file.save(f"{sop_uid}.dcm", dicom_file)

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
