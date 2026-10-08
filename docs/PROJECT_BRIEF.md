# Project brief

## Purpose and user journey

DocInsight aims to help a user organize private documents and answer questions from their contents. The intended journey is: sign in, create a collection, upload a supported document, inspect and optionally correct its extracted text, index it, ask a collection-scoped question, and inspect the original page and exact stored evidence behind each citation. Unsupported questions should receive an explicit insufficient-evidence outcome.

The domain is general: meeting notes, manuals, study material, policies, and similar records. The planned P0 input boundary is printed English in readable PDFs, scanned PDFs, and PNG/JPEG page images. Handwriting, diagrams, every language, and universal document accuracy are outside that boundary.

## Milestone

The owner chose the **specification MVP**, encompassing all P0 requirements in `DocInsight_SRS_Architecture.md`, rather than a reduced prototype. There is no fixed deadline; effort and sequencing will be reviewed as work proceeds. The specification's 15-day schedule is a proposal, not an approved delivery commitment. Early vertical slices may demonstrate partial behavior but must be labelled as such.

## Portfolio standard

The finished project should be demonstrable and explainable in technical interviews. Portfolio claims must be tied to implemented behavior and recorded checks. A valid citation link establishes provenance, while factual support requires separate inspection or evaluation. Account/session/token foundations and sender-admin permission exist with58 passing account tests. Document/OCR/RAG workflow and evaluation metrics remain unimplemented; no measured retrieval-quality result exists.
