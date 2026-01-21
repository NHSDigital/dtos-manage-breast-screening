from ninja import NinjaAPI

from manage_breast_screening.dicom.api import router as dicom_router

api = NinjaAPI(title="Manage Breast Screening API", version="1.0.0")
api.add_router("/dicom/", dicom_router)
