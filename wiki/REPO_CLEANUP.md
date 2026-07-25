# Repo Cleanup Log

> **Maintenance policy:** this file tracks the *current* cleanup state only.
> When a new cleanup pass happens, **update this file in place** — replace the
> log below with the latest activity. Do not append historical passes; git
> history is the archive, this file is the snapshot.

## Last cleanup: 2026-07-25 (complete legacy preprocessor baseline removal)

### What was done

**Files**
- Deleted the 3 root legacy shims `step1_preprocessor.py`,
  `step1_preprocessor_v2_full.py`, `step1_preprocessor_v3.py` — completes PR
  #107, which removed `wiki/legacy/*.py` but left the shims plus 20 test
  files importing them (main was red with 20 collection errors). Canonical
  `step1_preprocessor_v4.py` untouched.
- Migrated the 20 test files + conftest to the `impact_slides` package
  (facade re-export; monkeypatches retargeted to the owning submodules).
  Per-file dispositions and the one deleted test are documented in
  `tests/LEGACY_MIGRATION.md`.
- Two latent v4 decomposition bugs the migration surfaced were fixed in the
  same pass (dead stage-rule validation import; logger reset targeting a
  vestigial binding) — see commit `680709d`.
- Full suite green after the pass: 1190 passed, 15 skipped, 0 errors
  (was 804 collected + 20 errors).

### Environment notes (for future cleanups)
- The `no-mistakes` remote is a local bare mirror (`~/.no-mistakes/repos/`);
  deleting origin/local branches after PR merge is safe — pipeline custody
  lives in the mirror and CI monitors end at merge.
- `gh api` comment PATCH needs the *numeric* comment id (node ids 404);
  read gh output with `encoding="utf-8"` on this machine.

### Deferred (conscious, re-check next pass)
- `step4_builder_validator.py` consolidation (real refactor, not a sweep).
- `tests/test_renderer_v2_charts_js.py` split (~2,100 lines, grows every ticket).
- History scrub of old sim PNG blobs (~50MB of `.git`) — only if size becomes
  a real problem; rewrites hashes.

### Standing policies
- `simulation/` evidence lives only in GNHF worktrees, never on main
  (commit 1628633). Do not path-merge it back.
- Screenshot/evidence links in issues: pin to a commit SHA.
- Delete feature branches after PR merge (no-mistakes-safe once merged).
