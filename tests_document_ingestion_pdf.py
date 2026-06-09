from __future__ import annotations

from pathlib import Path

from winlocalassistant.document_ingestion import ingest_document, search_ingested_document


def test_pdf_ingestion_uses_pypdf_for_review_documents() -> None:
    path = Path("docs/NOVA_PROPOSED_CHANGES_AND_VALIDATION_V55_3_41.pdf")
    payload = ingest_document(path)

    assert payload["ok"] is True
    assert payload["converter"] == "pypdf"
    assert payload["chunk_count"] >= 1
    text = "\n".join(chunk["text"] for chunk in payload["chunks"])
    assert "WinLocalAssistant Proposed Changes" in text
    assert "honest image generation" in text


def test_pdf_ingestion_search_finds_validation_ladder() -> None:
    path = Path("docs/NOVA_v55_3_39_proposed_changes_and_validation_plan.pdf")
    payload = ingest_document(path)
    result = search_ingested_document(payload, "Validation ladder Playwright image generation")

    assert result["ok"] is True
    assert result["results"]
