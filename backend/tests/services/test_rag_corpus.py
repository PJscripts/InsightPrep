"""Tests for RAG knowledge corpus structure and metadata.

Validates that all project-authored markdown documents in docs/knowledge/
adhere to the frontmatter specification required by the future ingestion
pipeline and KnowledgeDocument SQLAlchemy model.
"""

import hashlib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_DIR = REPO_ROOT / "docs" / "knowledge"

EXPECTED_TOPICS = {"dsa", "dbms", "operating_systems", "computer_networks"}


def parse_frontmatter_and_body(file_path: Path) -> tuple[dict, str]:
    """Extract YAML frontmatter and markdown body from document."""
    content = file_path.read_text(encoding="utf-8")
    assert content.startswith("---"), (
        f"{file_path} must start with YAML frontmatter delimiter '---'"
    )
    parts = content.split("---", 2)
    assert len(parts) >= 3, (
        f"{file_path} must have closing YAML frontmatter delimiter '---'"
    )
    metadata = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return metadata, body


def test_knowledge_directory_structure():
    """Verify knowledge directory and topic subdirectories exist."""
    assert KNOWLEDGE_DIR.is_dir(), f"Missing directory: {KNOWLEDGE_DIR}"
    found_topics = {p.name for p in KNOWLEDGE_DIR.iterdir() if p.is_dir()}
    assert EXPECTED_TOPICS.issubset(found_topics)


def test_knowledge_documents_exist():
    """Verify each topic contains at least two documents."""
    for topic in EXPECTED_TOPICS:
        topic_dir = KNOWLEDGE_DIR / topic
        md_files = list(topic_dir.glob("*.md"))
        assert len(md_files) >= 2, (
            f"Topic '{topic}' should have at least 2 documents, found {len(md_files)}"
        )


def test_knowledge_document_metadata_and_hashes():
    """Verify frontmatter conforms to KnowledgeDocument model schema."""
    md_files = list(KNOWLEDGE_DIR.glob("**/*.md"))
    assert len(md_files) == 8, f"Expected 8 corpus documents, found {len(md_files)}"

    seen_keys = set()

    for file_path in md_files:
        metadata, body = parse_frontmatter_and_body(file_path)

        # Check required fields
        assert "source_key" in metadata, f"{file_path} missing source_key"
        assert "title" in metadata, f"{file_path} missing title"
        assert "topic" in metadata, f"{file_path} missing topic"
        assert "source_origin" in metadata, f"{file_path} missing source_origin"
        assert "source_license" in metadata, f"{file_path} missing source_license"

        # Check schema constraints matching KnowledgeDocument model
        source_key = metadata["source_key"]
        assert isinstance(source_key, str) and len(source_key) <= 100
        assert source_key not in seen_keys, f"Duplicate source_key: {source_key}"
        seen_keys.add(source_key)

        title = metadata["title"]
        assert isinstance(title, str) and 0 < len(title) <= 255

        topic = metadata["topic"]
        assert topic in EXPECTED_TOPICS
        folder_name = file_path.parent.name
        assert topic == folder_name, (
            f"Topic '{topic}' does not match folder '{folder_name}'"
        )

        source_origin = metadata["source_origin"]
        assert isinstance(source_origin, str) and len(source_origin) <= 255

        source_license = metadata["source_license"]
        assert source_license == "project-authored"

        # Verify body content exists and can compute content_hash (SHA-256)
        assert len(body) > 100, f"{file_path} body is too short"
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        assert len(content_hash) == 64
