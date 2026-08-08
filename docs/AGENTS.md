# docs

## Purpose

Agent-facing operating docs and durable engineering notes outside the code tree.

## Ownership

- `docs/agents/` — issue tracker, triage labels, domain-doc consumption rules, delegated delivery workflow
- `docs/adr/` — architectural decision records when present
- `docs/images/` — diagrams referenced by docs

## Local Contracts

- Tracker: GitHub Issues via `gh` on `xryptox/Impact_Slides` — see `agents/issue-tracker.md`
- Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` — see `agents/triage-labels.md`
- Domain intake: root `CONTEXT.md` + `docs/adr/`; do not invent parallel context files — see `agents/domain.md`
- Delegated delivery: manifest-driven wave startup/inspection, visible Herdr implementers, no-mistakes custody, host verification, approval-gated merger, and verified workflow cleanup — see `agents/delegated-delivery.md`
- PRs are **not** a request surface unless `issue-tracker.md` flips that flag

## Work Guidance

- Keep agent instructions operational and short
- Prefer updating these docs over burying process in chat or wiki plans

## Verification

- None automated; changes reviewed in PR/commit like any doc

## Child DOX Index

- No child AGENTS.md — `agents/` is small enough that this file owns it.
