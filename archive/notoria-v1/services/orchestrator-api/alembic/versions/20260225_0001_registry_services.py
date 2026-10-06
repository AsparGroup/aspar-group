"""create registry_services table with initial seed

Revision ID: 20260225_0001
Revises:
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260225_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "registry_services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("auth_type", sa.String(length=50), nullable=False, server_default="none"),
        sa.Column("auth_secret_ref", sa.String(length=255), nullable=True),
        sa.Column("endpoints", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("fallback_service", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_registry_services_category"), "registry_services", ["category"], unique=False)
    op.create_index(op.f("ix_registry_services_service_name"), "registry_services", ["service_name"], unique=True)
    op.create_index(op.f("ix_registry_services_type"), "registry_services", ["type"], unique=False)

    op.execute(
        """
        INSERT INTO registry_services
        (service_name, category, type, base_url, auth_type, auth_secret_ref, endpoints, limits, fallback_service, enabled)
        VALUES
        ('ltx_local','video','local','http://worker-video:80','none',NULL,'{"run":"/v1/run","health":"/healthz"}','{"concurrency":2,"timeout_s":120}', 'ltx_cloud', true),
        ('xtts_local','tts','local','http://worker-tts:80','none',NULL,'{"run":"/v1/run","health":"/healthz"}','{"concurrency":4,"timeout_s":60}', 'xtts_cloud', true),
        ('wav2lip_local','lipsync','local','http://worker-lipsync:80','none',NULL,'{"run":"/v1/run","health":"/healthz"}','{"concurrency":2,"timeout_s":90}', 'wav2lip_cloud', true),
        ('enhance_local','enhance','local','http://worker-enhance:80','none',NULL,'{"run":"/v1/run","health":"/healthz"}','{"concurrency":2,"timeout_s":120}', 'enhance_cloud', true),
        ('qa_local','qa','local','http://worker-qa:80','none',NULL,'{"run":"/v1/run","health":"/healthz"}','{"concurrency":8,"timeout_s":30}', 'qa_cloud', true),
        ('ltx_cloud','video','saas','https://video-cloud.placeholder.notoria','bearer','secrets/ltx_cloud_token','{"run":"/api/v1/render","health":"/api/v1/health"}','{"qps":10,"timeout_s":180}', NULL, false),
        ('xtts_cloud','tts','saas','https://tts-cloud.placeholder.notoria','bearer','secrets/xtts_cloud_token','{"run":"/api/v1/speech","health":"/api/v1/health"}','{"qps":20,"timeout_s":120}', NULL, false),
        ('wav2lip_cloud','lipsync','saas','https://lipsync-cloud.placeholder.notoria','bearer','secrets/wav2lip_cloud_token','{"run":"/api/v1/lipsync","health":"/api/v1/health"}','{"qps":10,"timeout_s":180}', NULL, false),
        ('enhance_cloud','enhance','saas','https://enhance-cloud.placeholder.notoria','bearer','secrets/enhance_cloud_token','{"run":"/api/v1/enhance","health":"/api/v1/health"}','{"qps":10,"timeout_s":180}', NULL, false),
        ('qa_cloud','qa','saas','https://qa-cloud.placeholder.notoria','bearer','secrets/qa_cloud_token','{"run":"/api/v1/check","health":"/api/v1/health"}','{"qps":30,"timeout_s":60}', NULL, false)
        ON CONFLICT (service_name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_registry_services_type"), table_name="registry_services")
    op.drop_index(op.f("ix_registry_services_service_name"), table_name="registry_services")
    op.drop_index(op.f("ix_registry_services_category"), table_name="registry_services")
    op.drop_table("registry_services")
