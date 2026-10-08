# Specification review

Source: `DocInsight_SRS_Architecture.md`, version 1.0. Read in full during the initial repository inspection. The repository initially contained only that file; no applicable `AGENTS.md` or Git repository existed.

## Requirements versus recommendations

P0 behavior is defined by DL-01 through DL-14 and the P0 release table: private accounts and collections; validated PDF/PNG/JPEG uploads; OCR and reviewable, correctable extraction; asynchronous indexing and retry; source-aware parent–child chunks; collection-scoped advanced retrieval; cited answers and source inspection; follow-up conversations; deletion; feedback; bounded provider use; and evaluation. The specification MVP also calls for a text PDF and scanned PDF to complete the flow, a second-user isolation check, and actual evaluation results. See `REQUIREMENT_TRACEABILITY.md` for each ID.

The owner approved Django/DRF, React/TypeScript/Vite, pinned lockfiles, and local Docker Compose development (D-005 and D-006). Recommendations still awaiting decisions include Tailwind, Router and TanStack Query; PostgreSQL/pgvector; Celery/Redis; Docling and an OCR engine; PDF.js-compatible viewing; model providers; the exact schema and API; chunk sizes, retrieval counts, fusion and context budgets; storage and deployment. Statements in the source's “Technical decisions” table did not become approvals merely by appearing there.

## Current scope interpretation

The owner chose the full specification MVP. No P0 requirement has been removed or deferred. The earlier short-prototype proposal was superseded before implementation. Partial development checkpoints will be distinguished from the completed MVP. See `PROTOTYPE_SCOPE.md` for this milestone record.

## Ambiguities and apparent conflicts to resolve

1. Editing a ready document is said to disable its old active index while replacement is built, while atomic publication describes switching to a complete new index. Define visibility during the gap and what `active_revision_id` means before schema and task work.
2. Retained answer provenance uses protected references, while deletion promises removal of files, text, vectors, and conversations. Define what remains visible in historical answers and what is removed by document versus collection deletion.
3. Corrected page text may not share offsets or reliable boxes with the original PDF. Define citation text, offsets, viewer highlights, and revision identity after correction.
4. “OCR only when needed” needs a detection rule, parser limits, and behavior for partially readable pages. The configured OCR engine is unspecified.
5. Model and embedding dimensions, where content leaves the app, budgets, and fallback behavior are unspecified.
6. The proposed question API supports optional document IDs; semantics for no IDs, mixed-ready documents, and deletion during generation need precise contracts.
7. The answer JSON describes `partial`, `insufficient_evidence`, and `needs_clarification`, but the exact display and evidence rules for each are not yet defined.
8. Collection deletion is required operationally but has no endpoint in the proposed API table. The retry, cleanup, and stuck-job recovery contracts need detail.
9. The specification estimates 32–38 focused DocInsight hours in a coordinated 15-day plan, but no delivery estimate has been validated against the current environment or approvals.
10. The proposed API returns 401 for unauthenticated requests, while DRF's standard `SessionAuthentication` uses 403 for denied unauthenticated requests. Decide whether to adapt the authentication/error response or revise the API contract; do not claim the proposed 401 behavior happens by default. See [DRF authentication documentation](https://www.django-rest-framework.org/api-guide/authentication/#unauthorized-and-forbidden-responses).

## Integration risks

- OCR parser installation, memory, scan quality, and page-layout errors.
- PostgreSQL/pgvector availability and fixed embedding dimensions before migrations.
- Worker idempotency and races involving correction, retry, deletion, and index publication.
- Provider cost, rate limits, latency, data exposure, and malformed model output.
- Private media delivery to the browser while retaining session authorization and PDF page navigation.
- Citation integrity across revisions, answers, and deletion.
- Time required to label approximately 50 mixed-document evaluation questions and reproduce results.

## Expensive-to-reverse decisions

Custom user model before first migration; database and vector dimension; extraction revision and index publication semantics; evidence IDs and citation references; deletion/provenance policy; and provider data boundary. These require review before dependent code or migrations.
