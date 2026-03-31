from __future__ import annotations

"""
Business rules for the JEPE QMS / ERP domain.

Conventions:
  - All deletes are soft-deletes (is_deleted=True). Hard deletes are forbidden.
  - Historical QMS records must never be purged.
  - Status transitions must follow the maps in domain.transitions.
  - UUIDs (Text) are used for all primary keys — never auto-increment Integer.
"""
