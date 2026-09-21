import uuid

from sqlalchemy.orm import Session

from app.models.device_model import DeviceModel
from app.models.device_vendor import DeviceVendor
from app.repositories.device_model_repository import DeviceModelRepository
from app.repositories.device_vendor_repository import DeviceVendorRepository


def list_vendors(db: Session) -> list[DeviceVendor]:
    return DeviceVendorRepository(db).list_active()


def list_models(db: Session, *, vendor_id: uuid.UUID | None = None) -> list[DeviceModel]:
    return DeviceModelRepository(db).list_active(vendor_id=vendor_id)
