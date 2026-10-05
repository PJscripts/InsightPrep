"""add rag knowledge tables

Revision ID: 7a14dcdb5c3e
Revises: 9f0f5d1b2c47
Create Date: 2026-10-04 12:36:30.252150

"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a14dcdb5c3e"
down_revision: Union[str, Sequence[str], None] = "9f0f5d1b2c47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pgvector extension and RAG knowledge tables."""

    # Enable pgvector extension (idempotent; safe to re-run).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create knowledge_documents table.
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("source_origin", sa.String(length=255), nullable=False),
        sa.Column(
            "source_license",
            sa.String(length=100),
            nullable=False,
            server_default="project-authored",
        ),
        sa.Column("source_path", sa.String(length=500), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", name="uq_knowledge_documents_source_key"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_topic"),
        "knowledge_documents",
        ["topic"],
        unique=False,
    )

    # Create knowledge_chunks table.
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunks_document_chunk",
        ),
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )

    # HNSW vector index for cosine similarity search.
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Remove RAG knowledge tables and indexes.

    The vector extension is intentionally NOT dropped: it is a
    database-level dependency that other tables, migrations, or manual
    additions may reference.  Dropping it would CASCADE-destroy every
    column of type ``vector`` in the database.
    """
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.drop_index(
        op.f("ix_knowledge_chunks_document_id"),
        table_name="knowledge_chunks",
    )
    op.drop_table("knowledge_chunks")
    op.drop_index(
        op.f("ix_knowledge_documents_topic"),
        table_name="knowledge_documents",
    )
    op.drop_table("knowledge_documents")
