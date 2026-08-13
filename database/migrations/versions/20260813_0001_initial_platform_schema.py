"""Create the initial CV platform persistence schema.

Revision ID: 20260813_0001
Revises: None
Create Date: 2026-08-13 00:00:00+00:00
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260813_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())
TIMESTAMP = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("password_salt", sa.LargeBinary(), nullable=False),
        sa.Column("password_hash", sa.LargeBinary(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('admin', 'developer', 'user')", name="ck_users_role"),
        sa.CheckConstraint("username = lower(username)", name="ck_users_username_lowercase"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_enabled", "users", ["enabled"])

    op.create_table(
        "user_sessions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", TIMESTAMP, nullable=False),
        sa.Column("revoked_at", TIMESTAMP),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
    )
    op.create_index("ix_user_sessions_user_expires", "user_sessions", ["user_id", "expires_at"])

    op.create_table(
        "projects",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_by", UUID, nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_projects_created_by", "projects", ["created_by"])

    op.create_table(
        "project_memberships",
        sa.Column("project_id", UUID, primary_key=True),
        sa.Column("user_id", UUID, primary_key=True),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("joined_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')", name="ck_memberships_role"),
    )
    op.create_index("ix_project_memberships_user", "project_memberships", ["user_id"])

    op.create_table(
        "algorithm_versions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("algorithm_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False, server_default=""),
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("task_type", sa.String(32), nullable=False),
        sa.Column("manifest", JSONB, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("image", sa.String(512), nullable=False),
        sa.Column("internal_port", sa.Integer(), nullable=False, server_default="8000"),
        sa.Column("package_storage_key", sa.String(1024)),
        sa.Column("package_sha256", sa.String(64)),
        sa.Column("image_digest", sa.String(256)),
        sa.Column("created_by", UUID),
        sa.Column("created_by_label", sa.String(128), nullable=False),
        sa.Column("traffic_weight", sa.SmallInteger(), nullable=False, server_default="100"),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", TIMESTAMP),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "task_type IN ('object_detection', 'classification', 'segmentation', 'ocr', 'pose_estimation')",
            name="ck_algorithm_versions_task_type",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded', 'validating', 'building', 'testing', 'available', 'disabled', 'failed')",
            name="ck_algorithm_versions_status",
        ),
        sa.CheckConstraint("internal_port BETWEEN 1 AND 65535", name="ck_algorithm_versions_port"),
        sa.CheckConstraint("traffic_weight BETWEEN 0 AND 100", name="ck_algorithm_versions_weight"),
        sa.UniqueConstraint("project_id", "algorithm_key", "version", name="uq_algorithm_version"),
    )
    op.create_index(
        "ix_algorithm_versions_project_status",
        "algorithm_versions",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_algorithm_versions_project_key",
        "algorithm_versions",
        ["project_id", "algorithm_key"],
    )

    op.create_table(
        "build_jobs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("algorithm_version_id", UUID, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("image_digest", sa.String(256)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["algorithm_version_id"], ["algorithm_versions.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'building', 'testing', 'completed', 'failed')",
            name="ck_build_jobs_status",
        ),
    )
    op.create_index("ix_build_jobs_version_created", "build_jobs", ["algorithm_version_id", "created_at"])

    op.create_table(
        "build_job_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("build_job_id", UUID, nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["build_job_id"], ["build_jobs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("build_job_id", "sequence", name="uq_build_job_logs_sequence"),
    )

    op.create_table(
        "image_assets",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("owner_id", UUID),
        sa.Column("owner_label", sa.String(128), nullable=False),
        sa.Column("original_name", sa.String(512), nullable=False),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column("algorithm_uri", sa.String(2048), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", TIMESTAMP),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("width > 0 AND height > 0", name="ck_image_assets_dimensions"),
        sa.CheckConstraint("size_bytes >= 0", name="ck_image_assets_size"),
        sa.UniqueConstraint("project_id", "storage_key", name="uq_image_assets_storage_key"),
    )
    op.create_index("ix_image_assets_project_created", "image_assets", ["project_id", "created_at"])
    op.create_index("ix_image_assets_project_sha256", "image_assets", ["project_id", "sha256"])

    op.create_table(
        "inference_tasks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("owner_id", UUID),
        sa.Column("owner_label", sa.String(128), nullable=False),
        sa.Column("algorithm_version_id", UUID, nullable=False),
        sa.Column("asset_id", UUID),
        sa.Column("asset_uri", sa.String(2048), nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("container_id", sa.String(128)),
        sa.Column("result_type", sa.String(32)),
        sa.Column("result", JSONB),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_of", UUID),
        sa.Column("cancelled_by", UUID),
        sa.Column("cancelled_by_label", sa.String(128)),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", TIMESTAMP),
        sa.Column("completed_at", TIMESTAMP),
        sa.Column("cancelled_at", TIMESTAMP),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["algorithm_version_id"], ["algorithm_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["asset_id"], ["image_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retry_of"], ["inference_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cancelled_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('queued', 'preparing', 'starting', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_inference_tasks_status",
        ),
    )
    op.create_index("ix_inference_tasks_project_created", "inference_tasks", ["project_id", "created_at"])
    op.create_index("ix_inference_tasks_project_status", "inference_tasks", ["project_id", "status"])
    op.create_index("ix_inference_tasks_algorithm", "inference_tasks", ["algorithm_version_id"])
    op.create_index("ix_inference_tasks_asset", "inference_tasks", ["asset_id"])

    op.create_table(
        "algorithm_comparisons",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("owner_id", UUID),
        sa.Column("owner_label", sa.String(128), nullable=False),
        sa.Column("asset_id", UUID, nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["asset_id"], ["image_assets.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_algorithm_comparisons_project_created", "algorithm_comparisons", ["project_id", "created_at"])

    op.create_table(
        "comparison_tasks",
        sa.Column("comparison_id", UUID, primary_key=True),
        sa.Column("task_id", UUID, primary_key=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["comparison_id"], ["algorithm_comparisons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["inference_tasks.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("position >= 0", name="ck_comparison_tasks_position"),
        sa.UniqueConstraint("comparison_id", "position", name="uq_comparison_tasks_position"),
    )

    op.create_table(
        "runtime_nodes",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("manager_url", sa.String(2048), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("manager_url", name="uq_runtime_nodes_manager_url"),
    )

    op.create_table(
        "runtime_instances",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("algorithm_version_id", UUID, nullable=False),
        sa.Column("node_id", sa.String(128), nullable=False),
        sa.Column("image", sa.String(512), nullable=False),
        sa.Column("container_name", sa.String(255), nullable=False),
        sa.Column("endpoint", sa.String(2048), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("device", sa.String(32), nullable=False),
        sa.Column("gpu_device_ids", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", TIMESTAMP),
        sa.ForeignKeyConstraint(["algorithm_version_id"], ["algorithm_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["runtime_nodes.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("node_id", "container_name", name="uq_runtime_instances_container"),
    )
    op.create_index("ix_runtime_instances_version_status", "runtime_instances", ["algorithm_version_id", "status"])
    op.create_index("ix_runtime_instances_node_status", "runtime_instances", ["node_id", "status"])

    op.create_table(
        "media_sources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("owner_id", UUID),
        sa.Column("owner_label", sa.String(128), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("uri", sa.String(2048), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("source_type IN ('video', 'rtsp', 'camera')", name="ck_media_sources_type"),
    )
    op.create_index("ix_media_sources_project_created", "media_sources", ["project_id", "created_at"])

    op.create_table(
        "media_inference_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("source_id", UUID, nullable=False),
        sa.Column("algorithm_version_id", UUID, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("interval_seconds", sa.Float(), nullable=False),
        sa.Column("max_frames", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_id"], ["media_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["algorithm_version_id"], ["algorithm_versions.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('queued', 'extracting', 'running', 'completed', 'failed')",
            name="ck_media_inference_runs_status",
        ),
        sa.CheckConstraint("interval_seconds > 0", name="ck_media_runs_interval"),
        sa.CheckConstraint("max_frames > 0", name="ck_media_runs_max_frames"),
    )
    op.create_index("ix_media_runs_project_created", "media_inference_runs", ["project_id", "created_at"])

    op.create_table(
        "media_run_tasks",
        sa.Column("media_run_id", UUID, primary_key=True),
        sa.Column("task_id", UUID, primary_key=True),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["media_run_id"], ["media_inference_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["inference_tasks.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("frame_index >= 0", name="ck_media_run_tasks_frame_index"),
        sa.UniqueConstraint("media_run_id", "frame_index", name="uq_media_run_tasks_frame"),
    )

    op.create_table(
        "workflows",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("created_by", UUID),
        sa.Column("created_by_label", sa.String(128), nullable=False),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("mode IN ('sequential', 'parallel')", name="ck_workflows_mode"),
    )
    op.create_index("ix_workflows_project_created", "workflows", ["project_id", "created_at"])

    op.create_table(
        "workflow_nodes",
        sa.Column("workflow_id", UUID, primary_key=True),
        sa.Column("node_key", sa.String(64), primary_key=True),
        sa.Column("algorithm_version_id", UUID, nullable=False),
        sa.Column("parameters", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["algorithm_version_id"], ["algorithm_versions.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("position >= 0", name="ck_workflow_nodes_position"),
        sa.UniqueConstraint("workflow_id", "position", name="uq_workflow_nodes_position"),
    )

    op.create_table(
        "workflow_node_dependencies",
        sa.Column("workflow_id", UUID, primary_key=True),
        sa.Column("node_key", sa.String(64), primary_key=True),
        sa.Column("depends_on_key", sa.String(64), primary_key=True),
        sa.ForeignKeyConstraint(
            ["workflow_id", "node_key"],
            ["workflow_nodes.workflow_id", "workflow_nodes.node_key"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id", "depends_on_key"],
            ["workflow_nodes.workflow_id", "workflow_nodes.node_key"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("node_key <> depends_on_key", name="ck_workflow_dependencies_not_self"),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("workflow_id", UUID, nullable=False),
        sa.Column("asset_id", UUID, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflows.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["asset_id"], ["image_assets.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_workflow_runs_status",
        ),
    )
    op.create_index("ix_workflow_runs_project_created", "workflow_runs", ["project_id", "created_at"])

    op.create_table(
        "workflow_run_tasks",
        sa.Column("workflow_run_id", UUID, primary_key=True),
        sa.Column("node_key", sa.String(64), primary_key=True),
        sa.Column("task_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["inference_tasks.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("task_id", name="uq_workflow_run_tasks_task"),
    )

    op.create_table(
        "autoscaling_policies",
        sa.Column("algorithm_version_id", UUID, primary_key=True),
        sa.Column("min_replicas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_replicas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("target_concurrency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("idle_seconds", sa.Integer(), nullable=False, server_default="1800"),
        sa.Column("updated_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["algorithm_version_id"], ["algorithm_versions.id"], ondelete="CASCADE"),
        sa.CheckConstraint("min_replicas >= 0", name="ck_autoscaling_min_replicas"),
        sa.CheckConstraint("max_replicas >= GREATEST(1, min_replicas)", name="ck_autoscaling_max_replicas"),
        sa.CheckConstraint("target_concurrency > 0", name="ck_autoscaling_target_concurrency"),
        sa.CheckConstraint("idle_seconds >= 30", name="ck_autoscaling_idle_seconds"),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("project_id", UUID),
        sa.Column("actor_id", UUID),
        sa.Column("actor_label", sa.String(128), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64)),
        sa.Column("resource_id", sa.String(128)),
        sa.Column("details", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status_code BETWEEN 100 AND 599", name="ck_audit_events_status_code"),
    )
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])
    op.create_index("ix_audit_events_project_created", "audit_events", ["project_id", "created_at"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("autoscaling_policies")
    op.drop_table("workflow_run_tasks")
    op.drop_table("workflow_runs")
    op.drop_table("workflow_node_dependencies")
    op.drop_table("workflow_nodes")
    op.drop_table("workflows")
    op.drop_table("media_run_tasks")
    op.drop_table("media_inference_runs")
    op.drop_table("media_sources")
    op.drop_table("runtime_instances")
    op.drop_table("runtime_nodes")
    op.drop_table("comparison_tasks")
    op.drop_table("algorithm_comparisons")
    op.drop_table("inference_tasks")
    op.drop_table("image_assets")
    op.drop_table("build_job_logs")
    op.drop_table("build_jobs")
    op.drop_table("algorithm_versions")
    op.drop_table("project_memberships")
    op.drop_table("projects")
    op.drop_table("user_sessions")
    op.drop_table("users")
