# RESEARCH — Improving `priority_score` for Legal Corpora

> Research + improvement plan (NO code changes). Root-caused why legal
> boilerplate outranks deal-relevance evidence in the AmEx × TheFork run, and
> designed config-driven fixes mirroring the existing `boost_keywords` /
> `stage_rules` / `MAX_TEXT_LENGTH` patterns.

---

## 1. Current `priority_score` mechanism

`priority_score` is assigned at evidence CREATION time (per-extractor), not
computed by a single function. There is no global scorer. Each extractor
hardcodes a base score, then `_apply_boost_rules()` applies user
`boost_keywords`, then the register is sorted descending.

### The scoring sites (preprocessor.py)

**Excel / PPTX** — computed via `calculate_evidence_priority_score()` (text_analysis.py:102) or flat values:
- `calculate_evidence_priority_score()` (text_analysis.py:102-127): base 0.5; +0.25 numeric / +0.20 categorical / +0.15 date; −0.25 if categorical & unique_ratio>0.7; −0.15 if no business name; +(non_null_ratio−0.5)*0.2. Identifier columns → flat 0.15.
- PPTX slide insight: `priority_for_evidence` from `pptx_profile.json` (line 1365).
- Flat values scattered: 0.82/0.85/0.87/0.88 for chart/table/outlier/correlation findings; 0.83 for aggregate_insight (line 855).

**PDF** (preprocessor.py:1630-1650 — the relevant path for this bug):
```python
base_priority = 0.62
if has_insight:
    base_priority = 0.78
if len(text) > 150:
    base_priority += 0.05
```
`has_insight = contains_insight_language(text) > 0.3` — where `text` is the
FULL page text (up to the 5000-char page-storage cap), NOT the truncated 800-char
evidence `text` field.

**DOCX** (preprocessor.py:1718) — **flat 0.60** for every paragraph >20 chars, regardless of content.

**Bullets** (preprocessor.py:1533) — `insight_priority_boost(bullet, 0.75)`:
base 0.75 + a boost proportional to `_INSIGHT_KEYWORDS` density (0→no boost,
≥4→+0.25, cap 0.98).

### The insight-language detector (text_analysis.py:51-68) — THE ROOT CAUSE
```python
insight_keywords = ['recommend','recommendation','key','critical','significant',
 'record','highest','lowest','growth','decline','risk','opportunity','important',
 'major','strongest','weakest','outperform','underperform','increase','decrease',
 'expand','reduce','improve','challenge','success','issue']
count = sum(1 for kw in insight_keywords if kw in text_lower)
return min(1.0, count / 4.0)   # >0.3 means ≥2 keyword hits
```
These are **substring** matches. `> 0.3` (i.e. ≥2 hits) ⇒ `has_insight=True` ⇒
base 0.78 ⇒ 0.83 with the length bonus.

### Post-creation adjustments
- `_apply_boost_rules()` (preprocessor.py:1923-1939): for each user `boost_keyword`
  found as substring in `text`, +0.15 (cap 0.98), stamps `boosted_by_rule`. **One-directional (up only); no downweight exists.**
- Per-type evidence caps (preprocessor.py:2029): `sorted(...)[:cap]` per
  insight_type (bullet≤20, pptx_slide≤15, table_cell≤12, etc.). Caps volume but
  does NOT rerank across files or downweight.
- Sort descending by `priority_score` (line 1727/1734/2031).

### Key file:line refs
- `impact_slides/text_analysis.py:51` — `contains_insight_language()` (the
  substring keyword detector that inflates legal prose).
- `impact_slides/text_analysis.py:73-99` — `_INSIGHT_KEYWORDS` +
  `insight_priority_boost()`.
- `impact_slides/text_analysis.py:102-127` — `calculate_evidence_priority_score()`.
- `impact_slides/preprocessor.py:1630-1650` — PDF page priority (0.62 / 0.78 / +0.05).
- `impact_slides/preprocessor.py:1718` — DOCX flat 0.60.
- `impact_slides/preprocessor.py:1923-1939` — `_apply_boost_rules()` (up-only).
- `impact_slides/preprocessor.py:2029` — per-type caps.

---

## 2. Root-cause diagnosis (from the AmEx × TheFork run)

**The gap:** top-10 by `priority_score` are ALL EX-10.1 acquisition-agreement
definition/boilerplate pages at **0.83**; the actual deal-rationale quotes
(Squeri, Marquez, Goldberg, the $232M/$28M financials) sit in DOCX at a **flat
0.60** — dead last.

```
Top by priority_score (all 0.83, all EX-10.1 boilerplate):
E0022 "Replacement Marks has the meaning set forth in Section 6.13(f)..."
E0023 "Seller Technology means all works of authorship..."
E0026 "references to any Person include the predecessor..."
E0047 "Group Companies have developed and maintained comprehensive..."
Deal-rationale (all 0.60 DOCX — dead last):
E0135 "Dining is one of the most important ways people engage..." (Marquez)
E0155 "shared strengths across dining, travel, and experiences" (Squeri)
E0157 "$232 million in revenue... $28 million adjusted EBITDA"
E0174 "Squeri said the deal also opens opportunities..."
```

**Why legal boilerplate scores 0.83:** `contains_insight_language()` runs on
the FULL page text (up to 5000 chars), and legal-agreement pages are long +
dense with words from the insight-keyword list that appear in LEGAL context:
`'risk'` (risk allocation), `'key'` (key definitions), `'important'` /
`'significant'` / `'critical'` / `'major'` (materiality clauses), `'issue'`
(issue of shares), `'record'` (records). ≥2 substring hits ⇒ `has_insight=True`
⇒ base 0.78 ⇒ 0.83 with the >150-char length bonus. The truncated 800-char
evidence `text` may not show these keywords (they appear later in the full
page), which is why a naive read of the register hides the cause.

**Why deal-rationale quotes score 0.60:** DOCX paragraphs get a **flat 0.60
regardless of content** (preprocessor.py:1718). The Marquez/Squeri quotes are
in DOCX press releases → flat 0.60, no insight boost, no length bonus. They
mathematically cannot outrank any PDF page with `has_insight=True`.

**The two compounding defects:**
1. `contains_insight_language()` keyword list is **domain-blind** — it cannot
   distinguish "risk" in a risk-allocation clause from "risk" in a strategic
   risk discussion. Legal prose triggers the "insight" boost falsely.
2. DOCX prose gets a **flat 0.60** with no content-aware boost, so genuinely
   high-narrative-value prose is capped below any PDF page that trips the
   insight-keyword heuristic.

### Evidence anchors
- `output/evidence_register_seed.json` E0022 (0.83, EX-10.1 "Replacement Marks"
  definition) vs E0135 (0.60, DOCX Marquez quote). Confirmed via
  `contains_insight_language()`: the keyword hits live in the full page text,
  not the truncated evidence text.
- Per-source average priority: EX-10.1.pdf 0.70 (n=86, with 16 pages at 0.83);
  all 5 DOCX sources 0.60 (n=47). The DOCX deal-rationale corpus is uniformly
  last.

---

## 3. Proposed approaches (design only — no implementation)

### Approach A — Legal-boilerplate downweight (inverse of boost_keywords)  ⭐ RECOMMENDED CORE
**Mechanism:** a configurable `downweight_keywords` list (plain substrings,
mirroring `boost_keywords`) AND a built-in `DEFAULT_LEGAL_BOILERPLATE_PATTERNS`
regex set (e.g. `r'"[^"]+"\s+means\s+`, `r"has the meaning set forth in`,
`r"Section \d+\.\d+`, `r"Indemnif`, `r"Reps and Warranties`,
`r"Group Companies"`, `r"Survival of"`). Evidence whose `text` matches a
downweight pattern → `priority_score − 0.20` (floor 0.10), stamped
`downweighted_by_rule`. This is the **exact inverse of `_apply_boost_rules()`**
and lives in a new `_apply_downweight_rules()` called right after
`_apply_boost_rules()` (preprocessor.py:1740).
**Effect on AmEx:** the 16 EX-10.1 definition pages at 0.83 → ~0.63, dropping
below the DOCX rationale. Boilerplate no longer dominates the top of the
register.
**Code sites:** `config.py` (add `downweight_keywords: []` to CONFIG_DEFAULTS
+ validation mirroring `boost_keywords`); `text_analysis.py` (add
`DEFAULT_LEGAL_BOILERPLATE_PATTERNS`); `preprocessor.py` (`__init__` reads
`self.downweight_keywords`, new `_apply_downweight_rules()` at ~1740,
`self.downweight_rules` built in a `_build_downweight_rules()` mirroring the
semantic_type pattern); `cli.py` (`--downweight-keywords` flag); README.
**Risks:** regex false-positives on legitimate "means" definitions in
non-legal docs (e.g. a glossary slide). Mitigation: the built-in patterns are
narrow (require `"`...`" means` or `Section N.N` form), and the keyword list is
user-overridable. **Corpus-generalizable** — not legal-only: the same mechanism
downweights any boilerplate the user names.

### Approach B — Narrative-relevance re-ranker (positive deal-signal boost)  ⭐ RECOMMENDED COMPANION
**Mechanism:** a configurable `relevance_keywords` list (default empty; user
provides deal-specific terms) that BOOSTS matching evidence +0.15 (like
`boost_keywords` but separate channel so both can fire). For the AmEx corpus
the user would set `--relevance-keywords "TheFork American Express acquisition
$700 million dining reservation"` → the Marquez/Squeri/financials DOCX entries
rise to 0.75, above boilerplate.
**Effect:** user-tunable, corpus-specific. Does not require the preprocessor to
"know" legal prose.
**Code sites:** identical pattern to `boost_keywords` (separate config key +
flag + rule pass). Could be folded into Approach A's rule pass for efficiency.
**Risks:** shifts the curation burden to the user (they must name the
deal-relevant terms). Low automation. Best used WITH Approach A, not instead.

### Approach C — Insight-keyword list refinement (fix the false-positive source)
**Mechanism:** split `contains_insight_language()`'s keyword list into
"strong insight" (`recommend, growth, decline, outperform, opportunity,
challenge, success, improve`) vs "weak/legal-ambiguous"
(`risk, key, important, significant, critical, major, issue, record`) and
require a STRONG hit (or ≥1 strong + ≥2 weak) for `has_insight=True`. Stops
legal pages from tripping the boost on weak-ambiguity words alone.
**Effect on AmEx:** EX-10.1 pages that only hit `risk`/`key`/`important` no
longer get 0.78 → drop to 0.62 (+0.05 length = 0.67). Still above DOCX 0.60,
so Approach A or B is still needed to fully reorder, but closes the false-positive.
**Code sites:** `text_analysis.py:51-68` (rewrite `contains_insight_language`).
**Risks:** changes the heuristic for ALL corpora — could regress
non-legal business decks where "key/important/significant" ARE genuine insight
signals. **High blast radius** (all PDF scoring changes). Needs careful test
review. v2/v3 have their own copies (frozen, unaffected) so baseline is safe,
but v4 tests asserting priority values (~50 assertions across 10 files) would
need review.

### Approach D — Per-file relative re-normalization / diversity reranker
**Mechanism:** after scoring, re-normalize so no single source file holds more
than X% of the top-N (e.g. top-30 must span ≥3 source files). Or rank within
each file then interleave. Prevents EX-10.1 (86 entries) from filling the top
by sheer volume.
**Effect:** guarantees source diversity at the top of the register regardless
of score. The Analyst GPT sees a balanced sample, not 30 pages of one agreement.
**Code sites:** a new `_diversity_rerank()` in `build_evidence_register()` after
the sort (preprocessor.py:~1734), before per-type caps.
**Risks:** can bury a legitimately high-value single-file corpus (e.g. one big
financial model). Should be optional (`--diversity-topn` / YAML) and off by
default to avoid changing baseline behavior. Does not fix the underlying
score inflation — only the symptom (top-N composition).

### Approach E — Insight_type / extraction_method re-weighting
**Mechanism:** per-insight-type priority multipliers in config (e.g.
`pdf_table_cell: 0.9x` when from a legal exhibit vs `0.6x`... but there's no
"legal exhibit" signal). More realistically: cap `pdf_page_insight` base at
0.70 unless `has_insight` is STRONG (approach C), and raise `docx_insight`
base from flat 0.60 to `insight_priority_boost(para, 0.70)` so content-bearing
DOCX prose can exceed boilerplate.
**Effect:** the DOCX flat-0.60 cap is the deepest defect — raising it to
content-aware 0.70-0.95 lets the Marquez quote (hits `important, growth,
success`) reach ~0.90, above boilerplate.
**Code sites:** preprocessor.py:1718 (DOCX), 1630 (PDF base). text_analysis for
the boost.
**Risks:** changing the DOCX flat 0.60 affects every DOCX-heavy run; test
fixtures with asserted DOCX priorities break. Moderate blast radius.

### Existing-mechanism audit (approach E continued)
- **No existing downweight/penalty** for prose. The only demote is
  `_looks_like_noise_cell()` (heuristics.py:146) for table cells (IP/URL/log).
- **No per-file cap / diversity reranker** — only per-insight-type count caps
  (preprocessor.py:2029).
- The PDF running-header/footer stripper (preprocessor.py:3346) strips
  recurring headers but NOT legal definition boilerplate.
- `boost_keywords` is up-only; there is no symmetric downweight.
⇒ Approach A is **net-new** (fills a real gap), not redundant.

---

## 4. Recommended approach

**Combine A + B + a targeted slice of E:**
1. **A (legal-boilerplate downweight)** — new `_apply_downweight_rules()`
   mirroring `_apply_boost_rules()`, with a built-in
   `DEFAULT_LEGAL_BOILERPLATE_PATTERNS` regex set + user
   `--downweight-keywords`. This is the highest-leverage, most-generalizable
   fix (the inverse of an existing, proven mechanism).
2. **E-targeted (raise DOCX flat 0.60 to `insight_priority_boost(para, 0.70)`)**
   — small, surgical: lets content-bearing DOCX prose outrank boilerplate
   without changing PDF scoring broadly. This alone closes most of the AmEx gap
   (Marquez quote → ~0.90).
3. **B (relevance_keywords)** — optional user-tunable positive boost for
   deal-specific terms; ship as a separate flag so users not running legal
   corpora aren't affected.

**Defer** C (insight-keyword split) and D (diversity reranker) — C has high
blast radius and needs a separate test-impact review; D treats the symptom not
the cause and should be opt-in.

All three recommended changes follow the project's config-precedence pattern
(CLI > YAML > default) and the schema-as-source-of-truth discipline, mirroring
the `boost_keywords` / `semantic_type_keywords` / `MAX_TEXT_LENGTH`
precedents.

### Exact code sites to change (for the implementation fork)
| Site | Change |
|---|---|
| `impact_slides/text_analysis.py` | add `DEFAULT_LEGAL_BOILERPLATE_PATTERNS` (list of compiled regexes); export. |
| `impact_slides/config.py` | add `downweight_keywords: []` + `relevance_keywords: []` to CONFIG_DEFAULTS; validate as list-of-str (mirror `boost_keywords`/`semantic_type_keywords`). |
| `impact_slides/preprocessor.py:__init__` | read `self.downweight_keywords`, `self.relevance_keywords`; build `self.downweight_rules` via `_build_downweight_rules()` (mirror `_build_semantic_type_rules`). |
| `impact_slides/preprocessor.py:~1740` | new `_apply_downweight_rules()` after `_apply_boost_rules()`; fold relevance boost into the same pass or a sibling `_apply_relevance_rules()`. |
| `impact_slides/preprocessor.py:1718` | DOCX: `"priority_score": insight_priority_boost(para, 0.70)` instead of flat `0.60`. |
| `impact_slides/cli.py` | `--downweight-keywords` + `--relevance-keywords` (nargs='*', mirror `--boost-keywords`); wire + rebuild rules in main(). |
| `README.md` + `config.example.yaml` | document both flags + the DOCX base change. |
| `tests/test_priority_legal.py` (new) | mirror `test_semantic_type.py`: constants, chokepoint (downweight applied, relevance boost, DOCX base), config, CLI. |

---

## 5. Test impact & regression risk

**v2/v3 baselines: SAFE.** `step1_preprocessor_v3.py` has its OWN embedded
`contains_insight_language()` (line 362) and its own scoring code — it does NOT
import `impact_slides/text_analysis.py` for scoring. Same for v2. Changes to the
v4 `text_analysis.py` / `preprocessor.py` scoring do NOT propagate to the
frozen baselines. **No v2/v3 regression.**

**v4 tests affected:** ~50 `priority_score` assertions across 10 test files
(test_evidence_post 9, test_helpers 8, test_intent 7, test_max_text_length 8,
test_realworld 5, test_schemas 5, test_v3 9 [v3 — SAFE], test_analyst_briefing
4, test_semantic_dedup 1, test_analytics 1, test_my_files 1, test_semantic_type
2). Of these:
- `test_v3.py` (9) → SAFE (tests the frozen v3 path).
- `test_realworld.py` (5) → reads realworld artifacts; if these were generated
  with the old scoring, the asserted priorities may shift after re-running
  v4. **Must regenerate the realworld fixtures** (like we did for
  `semantic_type`) and re-assert.
- `test_evidence_post.py`, `test_helpers.py`, `test_intent.py`,
  `test_max_text_length.py` → construct evidence with explicit `priority_score`
  values; mostly SAFE because they set the value directly (bypass the scorer),
  but any test that runs the full pipeline + asserts the SORT ORDER or the
  DOCX 0.60 base will need updating.
- The **DOCX base change (0.60 → content-aware 0.70)** is the riskiest: any
  test asserting `docx_insight` priority == 0.60 breaks. Needs a grep for
  `0.60` + `docx` in tests.

**Mitigation:** run the full suite after each change; the per-type cap +
downweight are additive (downweight only lowers, never raises), so most
existing assertions on constructed fixtures (which bypass the scorer) hold.
The DOCX base change is the one that needs a deliberate test update.

**Acceptance criteria for the implementation:**
- AmEx × TheFork run: top-10 by priority_score includes the Marquez/Squeri
  quotes and $232M financials (not dominated by EX-10.1 definitions).
- Full v4 suite: 505 passed + 8 skipped maintained (or updated fixtures).
- v2/v3 baseline: 469-equivalent maintained (unchanged).

---

## 6. Open questions for the user

1. **Approach A default patterns — legal-only or general?** Should
   `DEFAULT_LEGAL_BOILERPLATE_PATTERNS` ship enabled-by-default (risk:
   false-positives on non-legal decks with glossaries/"means" definitions) or
   opt-in via `--downweight-keywords` empty-by-default (safe, but the AmEx case
   needs the user to know to enable it)? **Recommendation:** ship the built-in
   patterns ON by default but gated behind a single `--no-downweight-boilerplate`
   escape hatch, since legal/contract corpora are a stated target use case.
2. **DOCX base change (0.60 → 0.70 content-aware)** — accept the test-fixture
   updates it forces? This is the highest-leverage single change but the
   riskiest for existing assertions.
3. **Approach C (insight-keyword split)** — defer (recommended) or include?
   It's the "purest" fix but has the broadest blast radius.
4. **Approach D (diversity reranker)** — worth adding as an opt-in `--diversity-topn`
   flag, or out of scope?
5. **Scope of this work:** implement A+B+DOCX-base now, or also C? This
   determines how many test fixtures need regeneration.
