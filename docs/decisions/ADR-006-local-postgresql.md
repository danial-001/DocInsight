# ADR-006: Local PostgreSQL and pgvector

**Status:** approved  
**Decision ID:** D-009

The owner approved option A and the foundation package with “Approved: D-009 A and WP-01a”. Option A uses PostgreSQL 17 with pgvector 0.8.6 from `pgvector/pgvector:0.8.6-pg17-bookworm`. Option B offered PostgreSQL 18 with the same extension. The recommendation was PostgreSQL 17 as a conservative starting point; the owner asked whether it could be accessed through pgAdmin 4, and desktop access through a localhost port was explained and included in the approval request.

Compose exposes the database only on 127.0.0.1, with a configurable host port and a named data volume. Django connects to the internal `db` host. Desktop pgAdmin connects to 127.0.0.1 using the host port and local database credentials. This approval does not authorize domain migrations, embedding dimensions, database constraints, or public database access. The owner did not state an additional rationale; none is inferred.
