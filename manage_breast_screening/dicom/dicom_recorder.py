import pydicom

from .models import Image, Series, Study


class DicomRecorder:
    @staticmethod
    def create_records(
        source_message_id: str, dicom_file: bytes
    ) -> tuple[Study, Series, Image] | None:
        ds = pydicom.dcmread(dicom_file)
        study_uid = ds.StudyInstanceUID
        series_uid = ds.SeriesInstanceUID
        sop_uid = ds.SOPInstanceUID

        study, _ = Study.objects.get_or_create(
            study_instance_uid=study_uid,
            defaults={
                "patient_id": getattr(ds, "PatientID", ""),
                "date": getattr(ds, "StudyDate", ""),
                "time": getattr(ds, "StudyTime", ""),
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
