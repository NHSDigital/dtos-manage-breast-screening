import pydicom
import pytest
from pydicom.uid import generate_uid
from pynetdicom.sop_class import (
    DigitalMammographyXRayImageStorageForPresentation,  # type: ignore
)


@pytest.fixture
def dataset():
    ds = pydicom.Dataset()
    ds.transfer_syntax_uid = pydicom.uid.ExplicitVRLittleEndian
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    ds.PatientID = "99912345"
    ds.StudyDate = "20240101"
    ds.StudyTime = "120000"
    ds.StudyDescription = "MAMMOGRAPHY"
    ds.Modality = "MG"
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1

    ds.file_meta = pydicom.Dataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = (
        DigitalMammographyXRayImageStorageForPresentation
    )
    ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID

    return ds
