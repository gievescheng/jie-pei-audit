# JEPE Audit System Refactor Brief

## Mission
Refactor this repository into a maintainable backend-first QMS/ERP system foundation without breaking current business direction.

## Current situation
- The repository mixes controlled QMS documents and application source code.
- Backend is currently FastAPI + SQLAlchemy.
- API routes are concentrated in one file.
- ORM models are concentrated in one file.
- Tests currently focus on smoke coverage and call Python API functions directly.
- The goal is not to redesign the business domain from scratch, but to create a clean execution foundation.

## Primary goal
Create a production-oriented backend structure that is:
- modular
- testable
- migration-friendly
- ready for auth/RBAC/audit/workflow
- ready for future frontend integration

## Hard constraints
- Do not delete historical QMS document folders.
- Do not rename or move QMS document folders in a way that breaks their archival meaning.
- Do not remove current working endpoints unless replaced with backward-compatible equivalents.
- Prefer incremental refactor over big-bang rewrite.
- Preserve business terms aligned to QMS / ERP / audit workflows.
- Avoid introducing unnecessary frameworks.

## Refactor priorities
1. Restructure backend package layout.
2. Separate route layer, service layer, repository/data-access layer, schema layer, and model layer.
3. Add API versioning.
4. Standardize error response and request tracing.
5. Introduce status enums and transition guards.
6. Prepare auth/RBAC extension points.
7. Replace direct schema creation dependency with migration-ready structure.
8. Upgrade test strategy:
   - unit tests
   - API integration tests
   - workflow tests
9. Add CI-ready quality gates.
10. Keep the repo usable at every stage.

## Non-goals for this phase
- Full frontend implementation
- Full document management module
- Full approval engine
- Full notification engine
- Full production scheduling engine

## Expected deliverables
- New backend folder architecture
- Refactored API modules
- Shared error/response utilities
- Domain enums and workflow/status guards
- Initial service layer
- Initial repository layer
- Migration scaffold
- Test scaffold with FastAPI TestClient
- Developer docs for local run/test/lint/migrate
- Upgrade plan for auth/audit/frontend phase

## Required output style
When executing:
- Make changes in small, reviewable commits
- Explain rationale in code comments only when valuable
- Update docs as you go
- Do not ask broad open-ended questions unless blocked by a hard ambiguity
- If blocked, make the safest assumption and continue, while documenting the assumption

## Definition of done
The refactor is done when:
- backend structure is modular
- current covered flows still work
- tests run consistently
- future modules can be added without returning to a giant single-file API design
