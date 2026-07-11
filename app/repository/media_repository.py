"""Media file repository for database CRUD operations."""

from app import models
from .base import BaseCRUD


class MediaRepository(BaseCRUD[models.MediaFile]):
    """Repository for MediaFile model."""

    def __init__(self):
        super().__init__(models.MediaFile)
