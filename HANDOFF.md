# HANDOFF.md

Use this file only for concise continuation context between substantial sessions or agents. Replace the active handoff when a newer one supersedes it; durable strategy belongs elsewhere.

## ACTIVE HANDOFF

**Date:** 2026-11-27
**From:** Claude Code (cloud session "Contrôler mon PC")
**To:** Claude Code on the CEO's Mac / next ASPAR agent

### Objective
Keep `AsparGroup/aspar-group` the single durable memory. This session audited that memory against the live master file and corrected what could be corrected from the repository.

### Read first
1. `STATE_ROUTER.md`, then `ETAT_LIVE_ASPAR.md` on Drive (step 0 of the reading order)
2. `ASPAR_CONTEXT.md`
3. `CURRENT_STATE.md`
4. `WORKBOARD.md`
5. `agent-os/README.md`
6. Relevant brand `SOURCE_LOCK.md`

### What changed
- `CURRENT_STATE.md` rewritten from the 2026-09-12 snapshot: what `agent-os/langgraph/` really contains, Odoo Cloud as the single Odoo target, instances declared by the CEO, known memory conflicts.
- Repository name aligned on `AsparGroup/aspar-group` in `CURRENT_STATE.md`, `README.md` and `agent-os/README.md`. The historical plan `docs/superpowers/plans/2026-09-12-consolidate-agent-os.md` keeps its original wording on purpose.
- `agent-os/README.md` reading order now starts at step 0, like `CLAUDE.md` and `AGENTS.md`.
- Verified on 2026-11-27 in a cloud session: `42 passed`, smoke `{"pass_path": "PASS", "status": "ok", "stop_path": "STOP"}` (Python 3.13).

### Decisions made
- 2026-11-27, CEO (in chat): set Notion aside for now. ADR 0001 stands; no Notion work until the CEO says otherwise. Recorded in `CURRENT_STATE.md`.

### Files changed
`CURRENT_STATE.md`, `HANDOFF.md`, `README.md`, `agent-os/README.md`.
`ETAT_LIVE_ASPAR.md` was read (REVISION 2, no active lock) and **not** modified.

### Blockers — decisions for the CEO
1. Update `ETAT_LIVE_ASPAR.md` §18 and the personal "Pilote technique" instructions, which still make Notion central and live outside this repository.
2. Give the address of ASPAR OS and confirm `agent.aspar.group` and `client.aspar.group`, then record the COO / ASPAR AGENT / ERP client / ASPAR OS split in `ETAT_LIVE_ASPAR.md` and, if it is a lasting decision, in a new ADR.
3. The Mac working copy (11 tests, `widget_snapshot`) has diverged from this repository (42 tests, no `widget_snapshot`). Decide which one is the base and push the missing side.
4. `WORKBOARD.md` NOW items do not mention REEFI, the active task in `ETAT_LIVE_ASPAR.md`. Arbitrate the priority.
5. Second-hand and unverified: a DNS check in another session reportedly showed `www.aspar.group` behind a tunnel to a local Odoo, which would contradict the Odoo-Cloud-only decision. Verify.

### Next exact action
1. From the Mac, compare the working copy with `origin/main` and push whatever is missing from `agent-os/langgraph/`.
2. Run `pytest` and the smoke runner there and update the Verification block of `CURRENT_STATE.md`.
3. Once the CEO answers the blockers above, update `ETAT_LIVE_ASPAR.md` following the lock protocol in `STATE_ROUTER.md`.

## HANDOFF TEMPLATE

```markdown
**Date:** YYYY-MM-DD
**From:** agent/session
**To:** agent/session

### Objective

### What changed

### Decisions made

### Files changed

### Blockers

### Next exact action
```
