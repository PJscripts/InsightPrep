"""Deterministic chunking for technical interview preparation documents."""

import re

from app.services.rag.document_loader import compute_content_hash
from app.services.rag.ingestion_types import IngestedChunk, ParsedDocument

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150

SECTION_SPLIT_REGEX = re.compile(r"(?:\r?\n)(?=#{1,3}\s+)")
PARAGRAPH_SPLIT_REGEX = re.compile(r"\n\s*\n")


class DocumentChunker:
    """Splits technical markdown documents preserving structure and section context."""

    def __init__(
        self,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: ParsedDocument) -> list[IngestedChunk]:
        """Split a ParsedDocument into deterministic IngestedChunk objects."""
        raw_chunks = self.split_text(document.body)
        ingested_chunks: list[IngestedChunk] = []

        for idx, text in enumerate(raw_chunks):
            clean_text = text.strip()
            if not clean_text:
                continue

            chunk_hash = compute_content_hash(clean_text)
            ingested_chunks.append(
                IngestedChunk(
                    chunk_index=idx,
                    chunk_text=clean_text,
                    content_hash=chunk_hash,
                )
            )

        return ingested_chunks

    def split_text(self, text: str) -> list[str]:
        """Split text hierarchically: headings -> paragraphs -> size budget."""
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return []

        # Step 1: Split into heading-delimited sections
        raw_sections = SECTION_SPLIT_REGEX.split(normalized)
        sections = [s.strip() for s in raw_sections if s.strip()]

        atomic_units: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                atomic_units.append(section)
            else:
                # Section exceeds chunk_size: split into paragraphs
                paras = PARAGRAPH_SPLIT_REGEX.split(section)
                for para in paras:
                    cleaned_p = para.strip()
                    if not cleaned_p:
                        continue
                    if len(cleaned_p) <= self.chunk_size:
                        atomic_units.append(cleaned_p)
                    else:
                        # Paragraph exceeds chunk_size: split by sentences / lines
                        lines = cleaned_p.split("\n")
                        for line in lines:
                            cleaned_line = line.strip()
                            if cleaned_line:
                                atomic_units.append(cleaned_line)

        # Step 2: Pack atomic units into chunks with configurable size and overlap
        chunks: list[str] = []
        current_chunk_parts: list[str] = []
        current_length = 0

        for unit in atomic_units:
            unit_len = len(unit)
            sep_len = 2 if current_chunk_parts else 0

            if current_length + sep_len + unit_len <= self.chunk_size:
                current_chunk_parts.append(unit)
                current_length += sep_len + unit_len
            else:
                if current_chunk_parts:
                    chunk_text = "\n\n".join(current_chunk_parts).strip()
                    if chunk_text:
                        chunks.append(chunk_text)

                    # Calculate overlap: retain tail units that fit within chunk_overlap
                    overlap_parts: list[str] = []
                    overlap_len = 0
                    for part in reversed(current_chunk_parts):
                        needed = len(part) + (2 if overlap_parts else 0)
                        if overlap_len + needed <= self.chunk_overlap:
                            overlap_parts.insert(0, part)
                            overlap_len += needed
                        else:
                            break

                    current_chunk_parts = list(overlap_parts)
                    current_length = sum(len(p) for p in current_chunk_parts) + (
                        2 * (len(current_chunk_parts) - 1)
                        if len(current_chunk_parts) > 1
                        else 0
                    )

                # Add the current unit
                if current_chunk_parts:
                    current_chunk_parts.append(unit)
                    current_length += 2 + unit_len
                else:
                    current_chunk_parts = [unit]
                    current_length = unit_len

        if current_chunk_parts:
            final_text = "\n\n".join(current_chunk_parts).strip()
            if final_text:
                chunks.append(final_text)

        return chunks
