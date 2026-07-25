# Repo Cleanup Log

> **Maintenance policy:** this file tracks the *current* cleanup state only.
> When a new cleanup pass happens, **update this file in place** — replace the
> log below with the latest activity. Do not append historical passes; git
> history is the archive, this file is the snapshot.

## Last cleanup: 2026-07-25 (post–Amex fidelity round 3)

### What was done

**Branches**
- Deleted stale/merged: `refactor/preprocessor-modular-v4`, `feature/theforkoutput`,
  `research/renderer-v2-gnhf-base` (local + origin), plus merged feature branches
  `feat/amex-p0-r2-callout-chrome`, `feat/amex-n2-ir-inbar-labels`,
  `feat/amex-n4-dual-stack-labels`, `feat/amex-n5-exterior-segment-columns`,
  `chore/drop-wiki-legacy`.
- Remaining: `main`, active feature branch, GNHF sim-worktree branch
  (`gnhf/objective-produce-a-9c5007` — v4 sim baseline, delete when v4 wraps).

**Files**
- `wiki/legacy/` removed (PR #107) — ~470KB duplicate preprocessor snapshots;
  history preserves them.
- Verified ignored: `output/`, `__pycache__/`, `simulation/`.

**GitHub issues**
- 11 screenshot comments on #96–#103 repointed from `.../main/simulation/...`
  (404 after the simulation/ drop) to pinned commit `.../7c66284/simulation/...`.
  Lesson: issue-comment assets must use commit-pinned URLs, never branch names.

**Git housekeeping**
- `git gc`: 1,974 loose objects → packed; `.git` 65MB → 54MB.
- `git remote prune origin`.

### Environment notes (for future cleanups)
- The `no-mistakes` remote is a local bare mirror (`~/.no-mistakes/repos/`);
  deleting origin/local branches after PR merge is safe — pipeline custody
  lives in the mirror and CI monitors end at merge.
- `gh api` comment PATCH needs the *numeric* comment id (node ids 404);
  read gh output with `encoding="utf-8"` on this machine.

### Deferred (conscious, re-check next pass)
- Root `step1_*` shims + `step4_builder_validator.py` consolidation
  (tests import the shims — real refactor, not a sweep).
- `tests/test_renderer_v2_charts_js.py` split (~2,100 lines, grows every ticket).
- History scrub of old sim PNG blobs (~50MB of `.git`) — only if size becomes
  a real problem; rewrites hashes.

### Standing policies
- `simulation/` evidence lives only in GNHF worktrees, never on main
  (commit 1628633). Do not path-merge it back.
- Screenshot/evidence links in issues: pin to a commit SHA.
- Delete feature branches after PR merge (no-mistakes-safe once merged).
