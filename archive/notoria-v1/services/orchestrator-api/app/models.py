from sqlalchemy import JSON, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class RegistryService(Base):
    __tablename__ = "registry_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    auth_secret_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    endpoints: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    limits: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fallback_service: Mapped[str | None] = mapped_column(String(120), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
