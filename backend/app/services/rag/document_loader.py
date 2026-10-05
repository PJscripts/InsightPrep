"""Markdown document discovery, frontmatter validation, and content hashing."""

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from app.services.rag.ingestion_types import ParsedDocument

FRONTMATTER_PATTERN = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.DOTALL)
REQUIRED_METADATA_FIELDS = (
    "source_key",
    "title",
    "topic",
    "source_origin",
    "source_license",
)


class DocumentParsingError(ValueError):
    """Raised when a document fails discovery, parsing, or metadata validation."""


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of normalized text."""
    normalized = text.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class MarkdownDocumentLoader:
    """Discovers and parses markdown documents with YAML frontmatter."""

    def __init__(self, repo_root: Path | None = None) -> None:
        if repo_root is None:
            # Backend root -> parent is repository root
            self.repo_root = Path(__file__).resolve().parents[4]
        else:
            self.repo_root = repo_root.resolve()

    def load_document(self, file_path: Path) -> ParsedDocument:
        """Parse a single markdown file into a validated ParsedDocument."""
        resolved_file = file_path.resolve()
        if not resolved_file.is_file():
            raise DocumentParsingError(f"File not found: {resolved_file}")

        try:
            content = resolved_file.read_text(encoding="utf-8")
        except Exception as exc:
            raise DocumentParsingError(
                f"Failed to read file as UTF-8: {resolved_file} ({exc})"
            ) from exc

        if not content.strip():
            raise DocumentParsingError(f"Document is empty: {resolved_file}")

        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            raise DocumentParsingError(
                "Document missing valid YAML frontmatter delimiters '---': "
                f"{resolved_file}"
            )

        raw_yaml, raw_body = match.group(1), match.group(2)

        try:
            metadata: Any = yaml.safe_load(raw_yaml)
        except Exception as exc:
            raise DocumentParsingError(
                f"Malformed YAML frontmatter in {resolved_file}: {exc}"
            ) from exc

        if not isinstance(metadata, dict):
            raise DocumentParsingError(
                f"Frontmatter must be a key-value mapping in {resolved_file}"
            )

        # Validate required metadata fields
        for field in REQUIRED_METADATA_FIELDS:
            val = metadata.get(field)
            if val is None or not str(val).strip():
                raise DocumentParsingError(
                    f"Missing or empty required metadata field '{field}' in "
                    f"{resolved_file}"
                )

        source_key = str(metadata["source_key"]).strip()
        if len(source_key) > 100:
            raise DocumentParsingError(
                f"source_key exceeds 100 characters in {resolved_file}"
            )

        title = str(metadata["title"]).strip()
        if len(title) > 255:
            raise DocumentParsingError(
                f"title exceeds 255 characters in {resolved_file}"
            )

        topic = str(metadata["topic"]).strip()
        if len(topic) > 100:
            raise DocumentParsingError(
                f"topic exceeds 100 characters in {resolved_file}"
            )

        source_origin = str(metadata["source_origin"]).strip()
        if len(source_origin) > 255:
            raise DocumentParsingError(
                f"source_origin exceeds 255 characters in {resolved_file}"
            )

        source_license = str(metadata["source_license"]).strip()
        if len(source_license) > 100:
            raise DocumentParsingError(
                f"source_license exceeds 100 characters in {resolved_file}"
            )

        normalized_body = raw_body.replace("\r\n", "\n").strip()
        if not normalized_body:
            raise DocumentParsingError(
                f"Document body is empty after frontmatter: {resolved_file}"
            )

        try:
            rel_path = resolved_file.relative_to(self.repo_root).as_posix()
        except ValueError:
            rel_path = resolved_file.as_posix()

        content_hash = compute_content_hash(normalized_body)

        return ParsedDocument(
            source_key=source_key,
            title=title,
            topic=topic,
            source_origin=source_origin,
            source_license=source_license,
            source_path=rel_path,
            content_hash=content_hash,
            body=normalized_body,
        )

    def discover_documents(self, corpus_dir: Path) -> list[ParsedDocument]:
        """Recursively discover and parse all markdown documents in directory."""
        resolved_dir = corpus_dir.resolve()
        if not resolved_dir.is_dir():
            raise DocumentParsingError(f"Corpus directory not found: {resolved_dir}")

        md_files = sorted(resolved_dir.glob("**/*.md"))
        documents: list[ParsedDocument] = []
        seen_keys: set[str] = set()

        for file_path in md_files:
            parsed = self.load_document(file_path)
            if parsed.source_key in seen_keys:
                raise DocumentParsingError(
                    f"Duplicate source_key detected: '{parsed.source_key}' in "
                    f"{file_path}"
                )
            seen_keys.add(parsed.source_key)
            documents.append(parsed)

        return documents
