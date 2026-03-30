# AGENT_BRIEF.md

## Project
JEPE Audit / QMS / ERP backend refactor

## Mission
Refactor this repository into a maintainable, backend-first QMS / ERP foundation for internal factory quality operations, while preserving current business direction and minimizing unnecessary back-and-forth.

---

## Current repository reality

This repository currently contains two different kinds of assets:

1. **Archival / controlled QMS documents**
   - Quality manual
   - Procedures
   - Forms
   - Records
   - Excel / Word / PDF operational materials

2. **Application source code**
   - Python backend
   - FastAPI
   - SQLAlchemy
   - Tests
   - Supporting utilities

The current backend is functional as an internal MVP, but the codebase is still at an early structure stage:
- route logic is too concentrated
- model definitions are too concentrated
- business rules are too thin
- test strategy is still early-stage
- the project is not yet ready for long-term scaling

The goal is **not** to redesign the business from zero.
The goal is to create a **clean execution foundation**.

---

## Primary objective

Transform the backend into a production-oriented structure that is:

- modular
- testable
- migration-friendly
- ready for auth / RBAC / audit / approval workflow
- ready for future frontend integration
- maintainable by a new engineer without needing project history in their head

---

## Absolute constraints

### Must preserve
- Historical QMS document folders and their archival meaning
- Existing backend business direction
- Existing covered flows unless safely replaced
- Business vocabulary aligned to QMS / ERP / audit workflows

### Must not do
- Do not perform a big-bang rewrite
- Do not aggressively move or rename archival document folders
- Do not delete working behavior without replacement
- Do not replace FastAPI
- Do not replace SQLAlchemy
- Do not introduce microservices
- Do not add unnecessary frameworks
- Do not ask repeated broad clarification questions unless truly blocked

### Assumption rule
If ambiguity is not blocking, make the safest reasonable assumption, document it, and continue.

---

## Refactor goals

### Goal 1: backend modularization
Replace the current oversized module style with a maintainable layered structure.

### Goal 2: clear architectural separation
Separate:
- API layer
- service layer
- repository / data access layer
- schema layer
- model layer
- shared core utilities
- domain rules / enums / transitions

### Goal 3: future-readiness
Prepare extension points for:
- authentication
- role-based access control
- audit logging
- approval workflow
- notifications
- frontend integration
- document control module

### Goal 4: quality and delivery discipline
Ensure the project can be:
- tested
- migrated
- reviewed
- extended without collapsing back into a single giant file design

---

## Required target architecture

Use this as the intended structure unless a slightly different equivalent structure is clearly better.

```text
erp_qms_core/
  backend/
    app/
      main.py
      api/
        v1/
          router.py
          health.py
          customers.py
          suppliers.py
          products.py
          bom.py
          orders.py
          inventory.py
          shipments.py
      core/
        config.py
        db.py
        errors.py
        logging.py
        responses.py
        request_context.py
        security.py
      domain/
        enums.py
        transitions.py
        rules.py
      models/
        __init__.py
        base.py
        master.py
        orders.py
        inventory.py
        audit.py
      repositories/
        __init__.py
        customers.py
        suppliers.py
        products.py
        bom.py
        orders.py
        inventory.py
        shipments.py
      schemas/
        __init__.py
        common.py
        customers.py
        suppliers.py
        products.py
        bom.py
        orders.py
        inventory.py
        shipments.py
      services/
        __init__.py
        customers.py
        suppliers.py
        products.py
        bom.py
        sales_orders.py
        work_orders.py
        inventory.py
        shipments.py
        audit.py
    tests/
      unit/
      integration/
      workflows/
    migrations/
    README.md
    requirements.txt
    requirements-dev.txt
    alembic.ini
