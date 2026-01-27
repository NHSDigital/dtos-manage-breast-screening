import random

import numpy as np
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
    # Image information
    ds.InstanceNumber = 1

    # Add some basic image pixel data
    # For demonstration, create a simple test pattern
    rows, cols = 256, 256
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1  # Signed
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"

    # Create simple test pattern pixel data
    pixel_data = np.zeros((rows, cols), dtype=np.int16)

    # Add some pattern to make it more realistic
    for i in range(rows):
        for j in range(cols):
            # Create a pattern with random values and some gradients
            base_value = random.randint(-1000, 2000)
            gradient_x = int((j / cols) * 500)
            gradient_y = int((i / rows) * 500)
            circle_value = 0
            center_x, center_y = rows // 2, cols // 2
            distance = ((i - center_x) ** 2 + (j - center_y) ** 2) ** 0.5
            if distance < min(rows, cols) // 4:
                circle_value = 1000

            pixel_data[i, j] = base_value + gradient_x + gradient_y + circle_value

    # Add noise
    noise = np.random.normal(0, 50, (rows, cols)).astype(np.int16)
    pixel_data = pixel_data + noise

    ds.PixelData = pixel_data.tobytes()

    return ds
