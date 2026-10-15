"""Ingest triage PDF references into Neon/Postgres as traceable source documents.

The application uses the extracted text and metadata as reference material only.
It does not convert these references into diagnoses or clinical authority.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from typing import Any

from sqlalchemy.orm import Session

from app.models.flow import TriageSourceDocument


PDF_METADATA: dict[str, dict[str, Any]] = {
    "card.pdf": {
        "title": "Interagency Integrated Triage Tool: Reference Card",
        "source_type": "clinical_protocol_reference",
        "publisher": "World Health Organization, Médecins Sans Frontières, and International Committee of the Red Cross",
        "license": "CC BY-NC-SA 3.0 IGO",
        "source_url": "https://www.who.int/emergencycare",
    },
    "iitt_adult.pdf": {
        "title": "Interagency Integrated Triage Tool: Age >= 12",
        "source_type": "clinical_protocol_reference",
        "publisher": "World Health Organization, International Committee of the Red Cross, Médecins Sans Frontières",
        "license": "CC BY-NC-SA 3.0 IGO",
        "source_url": "https://www.who.int/emergencycare",
    },
    "iitt_pediatric.pdf": {
        "title": "Interagency Integrated Triage Tool: Age < 12",
        "source_type": "clinical_protocol_reference",
        "publisher": "World Health Organization, International Committee of the Red Cross, Médecins Sans Frontières",
        "license": "CC BY-NC-SA 3.0 IGO",
        "source_url": "https://www.who.int/emergencycare",
    },
    "mass-casualty---iitt.pdf": {
        "title": "Mass Casualty - Interagency Integrated Triage Tool",
        "source_type": "clinical_protocol_reference",
        "publisher": "World Health Organization, International Committee of the Red Cross, Médecins Sans Frontières",
        "license": "CC BY-NC-SA 3.0 IGO",
        "source_url": "https://www.who.int/emergencycare",
    },
    "mcm-triage_guidance-note.pdf": {
        "title": "Facility-Based Mass Casualty Triage Guidance Note",
        "source_type": "operational_guidance_reference",
        "publisher": "World Health Organization Academy",
        "license": "WHO publication reference",
        "source_url": "https://www.who.int/emergencycare",
    },
}


def extract_pdf_text(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", path, "-"],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def sha256_file(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_source_document(db: Session, filename: str, pdf_dir: str) -> TriageSourceDocument | None:
    metadata = PDF_METADATA.get(filename)
    if not metadata:
        return None
    title = metadata["title"]
    existing = db.query(TriageSourceDocument).filter(TriageSourceDocument.title == title).first()
    path = os.path.join(pdf_dir, filename)
    extracted_text = extract_pdf_text(path)
    content_hash = sha256_file(path)
    if existing:
        if extracted_text and (not existing.extracted_text or existing.content_sha256 != content_hash):
            existing.extracted_text = extracted_text
            existing.content_sha256 = content_hash
            existing.ingestion_status = "ingested"
            db.commit()
            db.refresh(existing)
        return existing

    document = TriageSourceDocument(
        title=title,
        source_type=metadata["source_type"],
        source_url=metadata.get("source_url"),
        license=metadata.get("license"),
        publisher=metadata.get("publisher"),
        published_date=None,
        extracted_text=extracted_text,
        content_sha256=content_hash,
        ingestion_status="ingested" if extracted_text else "metadata_only",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def ingest_triage_sources(db: Session, pdf_dir: str) -> list[TriageSourceDocument]:
    docs = []
    for filename in sorted(PDF_METADATA):
        doc = ensure_source_document(db, filename, pdf_dir)
        if doc:
            docs.append(doc)
    return docs
