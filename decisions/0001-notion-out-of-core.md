# ADR 0001 — Notion outside ASPAR core infrastructure

**Status:** ACTIVE  
**Date:** 2026-09-11

## Context
Notion was previously used heavily for ASPAR Business modelling, relational databases and knowledge/workflow experiments. Over time it became an additional overlapping system beside Odoo, GitHub, Drive and other tools. Maintaining another paid operational layer increased cost and fragmentation without a unique core function.

## Decision
Notion is no longer part of ASPAR core infrastructure.

Allowed uses:
- legacy/reference access to existing work;
- demonstration of Notion expertise;
- client missions where Notion is specifically appropriate;
- temporary/manual work when it does not create a competing source of truth.

Notion must not become the canonical store for ASPAR group decisions, runtime business operations or the shared AI memory.

## Consequences
- Durable ASPAR strategy/context moves to GitHub Markdown.
- Operational business records belong primarily in Odoo where relevant.
- Existing Notion work is preserved; it is not deleted merely because its architectural role changed.
- New Notion databases require a concrete client/business reason, not architectural habit.

## Supersedes
Any prior implicit assumption that Notion should serve as ASPAR's central internal operating/knowledge database.
