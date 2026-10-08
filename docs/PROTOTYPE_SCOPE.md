# Scope and demonstration status

This file retains the requested name for continuity. **There is no approved reduced prototype.** The owner chose to pursue the full specification MVP. The earlier text-PDF prototype proposal and its suggested P0 deferrals were superseded before implementation. No P0 deferral is approved.

## Target scope

All DL-01 through DL-14 requirements and the P0 release boundaries in `DocInsight_SRS_Architecture.md` remain in scope. A completed MVP must include private user access; collection lifecycle; PDF/PNG/JPEG validation; text extraction and scanned-page OCR; review and correction with revisions; asynchronous jobs and safe retry; source-aware parent–child indexing; hybrid retrieval and reranking; cited collection-scoped answers, follow-ups, and source inspection; deletion, feedback, and provider bounds; plus reproducible evaluation and checks.

The specification's exclusions still apply: no promise of handwriting, multilingual support, complex numerical table analysis, universal accuracy, streaming, sharing, DOCX, entity GraphRAG, or public deployment as a default. These are specification boundaries, not newly deferred P0 items.

## Demonstration and acceptance

The eventual demo should show a fresh user upload a text PDF and a scanned document, review extracted text, ask a supported and an unsupported question, and open exact page-linked evidence. A second user must be unable to access the first user's collections, files, answers, or citations. Correction must produce a new revision and new retrieval behavior. Job retry must avoid duplicate active indexes. Actual results are required before claiming these behaviors work.

## Genuine integrations and simulations

No integrations or simulations exist yet. Every later fixture, fake model, or simulated result must be labelled in the relevant component documentation, test record, README, and demo notes. A partial checkpoint will list the specific implemented and verified behavior; it will never be called the completed specification MVP.
