from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage


def test_local_file_storage_generates_valid_urls(tmp_path):
    storage = FileSystemStorage(location=tmp_path, base_url="/dicom/")
    filename = storage.save("test.jpg", ContentFile(b"fake image data"))
    assert storage.url(filename).startswith("/dicom/")
