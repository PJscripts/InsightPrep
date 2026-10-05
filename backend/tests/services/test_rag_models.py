"""Database-independent tests for RAG knowledge models.

These tests verify SQLAlchemy model metadata — table names, column types,
foreign keys, constraints, relationships, and vector dimensions — without
requiring a live PostgreSQL connection.
"""

import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, inspect

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument

# ---------------------------------------------------------------------------
# KnowledgeDocument model tests
# ---------------------------------------------------------------------------


class TestKnowledgeDocumentModel:
    """Verify KnowledgeDocument metadata without a database."""

    def test_tablename(self):
        assert KnowledgeDocument.__tablename__ == "knowledge_documents"

    def test_primary_key(self):
        mapper = inspect(KnowledgeDocument)
        pk_cols = [col.name for col in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_required_columns_exist(self):
        mapper = inspect(KnowledgeDocument)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id",
            "source_key",
            "title",
            "topic",
            "source_origin",
            "source_license",
            "source_path",
            "content_hash",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names), (
            f"Missing columns: {expected - column_names}"
        )

    def test_source_key_is_unique(self):
        table = KnowledgeDocument.__table__
        source_key_col = table.c.source_key
        assert source_key_col.unique is True

    def test_source_key_is_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.source_key.nullable is False

    def test_topic_is_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.topic.nullable is False

    def test_source_origin_is_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.source_origin.nullable is False

    def test_source_license_is_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.source_license.nullable is False

    def test_source_license_default(self):
        table = KnowledgeDocument.__table__
        col = table.c.source_license
        # Python-side default from the model
        assert col.default is not None
        assert col.default.arg == "project-authored"

    def test_source_path_is_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.source_path.nullable is True

    def test_content_hash_is_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.content_hash.nullable is False

    def test_content_hash_length(self):
        table = KnowledgeDocument.__table__
        col = table.c.content_hash
        assert isinstance(col.type, String)
        assert col.type.length == 64

    def test_timestamp_columns_use_datetime_type(self):
        table = KnowledgeDocument.__table__
        assert isinstance(table.c.created_at.type, DateTime)
        assert isinstance(table.c.updated_at.type, DateTime)

    def test_timestamp_columns_are_not_nullable(self):
        table = KnowledgeDocument.__table__
        assert table.c.created_at.nullable is False
        assert table.c.updated_at.nullable is False

    def test_timestamps_use_naive_utc_defaults(self):
        """Timestamps use Python-side datetime.utcnow, matching existing models."""
        table = KnowledgeDocument.__table__
        assert table.c.created_at.default is not None
        default_arg = table.c.created_at.default.arg
        created_arg = getattr(default_arg, "__wrapped__", default_arg)
        assert created_arg == datetime.datetime.utcnow
        assert table.c.updated_at.default is not None
        update_arg = table.c.updated_at.default.arg
        updated_arg = getattr(update_arg, "__wrapped__", update_arg)
        assert updated_arg == datetime.datetime.utcnow

    def test_chunks_relationship_exists(self):
        mapper = inspect(KnowledgeDocument)
        rel_names = {r.key for r in mapper.relationships}
        assert "chunks" in rel_names

    def test_chunks_relationship_cascade_includes_delete(self):
        mapper = inspect(KnowledgeDocument)
        chunks_rel = mapper.relationships["chunks"]
        assert "delete" in chunks_rel.cascade


# ---------------------------------------------------------------------------
# KnowledgeChunk model tests
# ---------------------------------------------------------------------------


class TestKnowledgeChunkModel:
    """Verify KnowledgeChunk metadata without a database."""

    def test_tablename(self):
        assert KnowledgeChunk.__tablename__ == "knowledge_chunks"

    def test_primary_key(self):
        mapper = inspect(KnowledgeChunk)
        pk_cols = [col.name for col in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_required_columns_exist(self):
        mapper = inspect(KnowledgeChunk)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id",
            "document_id",
            "chunk_index",
            "chunk_text",
            "content_hash",
            "embedding",
            "created_at",
        }
        assert expected.issubset(column_names), (
            f"Missing columns: {expected - column_names}"
        )

    def test_document_id_foreign_key(self):
        table = KnowledgeChunk.__table__
        col = table.c.document_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "knowledge_documents.id" in fk_targets

    def test_document_id_cascade_delete(self):
        table = KnowledgeChunk.__table__
        col = table.c.document_id
        for fk in col.foreign_keys:
            if fk.target_fullname == "knowledge_documents.id":
                assert fk.ondelete == "CASCADE"

    def test_document_id_is_not_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.document_id.nullable is False

    def test_chunk_index_is_not_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.chunk_index.nullable is False

    def test_chunk_text_is_not_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.chunk_text.nullable is False

    def test_content_hash_is_not_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.content_hash.nullable is False

    def test_embedding_is_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.embedding.nullable is True

    def test_embedding_is_vector_384(self):
        table = KnowledgeChunk.__table__
        col = table.c.embedding
        assert isinstance(col.type, Vector)
        assert col.type.dim == 384

    def test_timestamp_uses_datetime_type(self):
        table = KnowledgeChunk.__table__
        assert isinstance(table.c.created_at.type, DateTime)

    def test_timestamp_is_not_nullable(self):
        table = KnowledgeChunk.__table__
        assert table.c.created_at.nullable is False

    def test_timestamp_uses_naive_utc_default(self):
        table = KnowledgeChunk.__table__
        assert table.c.created_at.default is not None
        default_arg = table.c.created_at.default.arg
        created_arg = getattr(default_arg, "__wrapped__", default_arg)
        assert created_arg == datetime.datetime.utcnow

    def test_unique_constraint_on_document_chunk(self):
        table = KnowledgeChunk.__table__
        constraint_names = {
            c.name for c in table.constraints if hasattr(c, "name") and c.name
        }
        assert "uq_knowledge_chunks_document_chunk" in constraint_names

    def test_document_relationship_exists(self):
        mapper = inspect(KnowledgeChunk)
        rel_names = {r.key for r in mapper.relationships}
        assert "document" in rel_names


# ---------------------------------------------------------------------------
# Model registration tests
# ---------------------------------------------------------------------------


class TestModelRegistration:
    """Verify new models are registered with Base.metadata."""

    def test_knowledge_documents_in_metadata(self):
        from app.core.database import Base

        assert "knowledge_documents" in Base.metadata.tables

    def test_knowledge_chunks_in_metadata(self):
        from app.core.database import Base

        assert "knowledge_chunks" in Base.metadata.tables

    def test_models_importable_from_package(self):
        from app.models import KnowledgeChunk as KC
        from app.models import KnowledgeDocument as KD

        assert KC.__tablename__ == "knowledge_chunks"
        assert KD.__tablename__ == "knowledge_documents"
