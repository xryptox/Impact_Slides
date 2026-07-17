#!/usr/bin/env python3
"""Generator for the Impact Slide Renderer (Step 4) output on the AmEx/TheFork corpus.

Implements the patched Renderer prompt:
  1. Working deck JS (stage scaler + .active switching + keyboard nav + buttons + Notes toggle + DECK_META)
  2. No section tags (Why/What/How/Now) on slides — internal only
  3. Zero evidence IDs on any visible slide (data_table Source column dropped)
  4. Slide-1 quote_card inserted as slide 2 (deck grows 14 -> 15)
"""
import json, html, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
BASE = r"C:/Users/Ag1Le/Documents/realworld_test/amex_thefork_acquisition"
HANDOFF = os.path.join(BASE, "builder_handoff_detection", "builder_handoff.json")
SEED = os.path.join(BASE, "output_v4_detection_v2", "evidence_register_seed.json")
OUT = os.path.join(BASE, "renderer_handoff")

# ---------- load inputs ----------
d = json.load(open(HANDOFF, encoding="utf-8"))
seed = json.load(open(SEED, encoding="utf-8"))
lk = {x["evidence_id"]: x for x in seed}
P = d["presentation"]
orig_slides = d["slides"]

# ---------- helpers ----------
def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)

def strip_ids(s):
    """Remove (E####) and (E####, E####) parenthesized ID lists from visible text."""
    if not s:
        return s
    s = re.sub(r"\(E\d{4}(?:\s*,\s*E\d{4})*\)", "", s)
    s = re.sub(r"\(E\d{4}(?:\s*/\s*E\d{4})+\)", "", s)  # E0104/E0121
    s = re.sub(r"\(\s*,\s*", "(", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s

def ev_text(eid, n=160):
    ev = lk.get(eid, {})
    t = (ev.get("text") or "").replace("\n", " ").strip()
    if len(t) > n:
        t = t[:n].rstrip() + "…"
    return t

def ev_source(eid):
    return lk.get(eid, {}).get("source_file", "?")

def ev_conf(eid):
    return lk.get(eid, {}).get("confidence", "medium")

# ---------- build slide list with the slide-1 quote_card insertion ----------
# Original S1 = quote_card -> becomes inserted slide 2 (quote_card).
# New slide 1 = title_or_opening (deck cover).
# Originals S2..S14 become new slides 3..15.
slides = []

# --- new slide 1: title_or_opening (deck cover) ---
s1_orig = orig_slides[0]
title_cover = {
    "slide_number": 1,
    "section": "Why",
    "layout_type": "title_or_opening",
    "title": P["title"],
    "subtitle": P.get("subtitle", "") or s1_orig.get("audience_takeaway", ""),
    "headline": "",
    "audience": P.get("audience", ""),
    "primary_goal": P.get("primary_goal", ""),
    "content": {},
    "evidence_sources": s1_orig.get("evidence_sources", []),
    "speaker_notes": s1_orig.get("speaker_notes", ""),
    "_orig": 1,
}
slides.append(title_cover)

# --- new slide 2: inserted quote_card (the executive quotes from original S1) ---
s1_content = s1_orig.get("content", {})
s1_pv = (s1_orig.get("visual_spec") or {}).get("primary_visual", {})
quote_slide = {
    "slide_number": 2,
    "section": "Why",
    "layout_type": "quote_card",
    "title": s1_orig["title"],
    "subtitle": "",
    "headline": s1_content.get("headline", ""),
    "content": {"body_text": s1_content.get("body_text", "")},
    "primary_visual": s1_pv,
    "evidence_sources": s1_orig.get("evidence_sources", []),
    "speaker_notes": s1_orig.get("speaker_notes", ""),
    "_orig": 1,
    "_inserted": True,
}
slides.append(quote_slide)

# --- originals S2..S14 -> new slides 3..15 ---
for s in orig_slides[1:]:
    ns = dict(s)
    ns["slide_number"] = s["slide_number"] + 1
    ns["_orig"] = s["slide_number"]
    slides.append(ns)

TOTAL = len(slides)

# ---------- component CSS ----------
CSS = """
/* viewport-base.css (from frontend-slides) */
html, body { width:100%; height:100%; margin:0; overflow:hidden; background:var(--stage-bg,#0b0f1a); }
.deck-viewport { position:fixed; inset:0; overflow:hidden; background:var(--stage-bg,#0b0f1a); }
.deck-stage { position:absolute; left:0; top:0; width:1920px; height:1080px; overflow:hidden; transform-origin:0 0; background:var(--slide-bg,#fff); }
.slide { position:absolute; inset:0; width:1920px; height:1080px; overflow:hidden; display:block; visibility:hidden; opacity:0; pointer-events:none; background:var(--slide-bg,#fff); }
.slide.active, .slide.visible { visibility:visible; opacity:1; pointer-events:auto; z-index:1; }
img, video, canvas, svg { max-width:100%; max-height:100%; }
.deck-controls { position:fixed; left:50%; bottom:22px; transform:translateX(-50%); z-index:1000; display:flex; gap:10px; align-items:center; font-family:var(--font-body); }
.deck-controls button { background:rgba(11,15,26,.85); color:#fff; border:1px solid rgba(255,255,255,.18); border-radius:8px; padding:8px 14px; font-size:15px; cursor:pointer; }
.deck-controls button:hover { background:rgba(30,80,160,.9); }
.deck-controls #counter { color:#cdd6e6; font-size:14px; min-width:70px; text-align:center; }
@media print {
  html,body{ width:1920px; height:auto; overflow:visible; background:#fff; }
  .deck-viewport{ position:static; overflow:visible; background:#fff; }
  .deck-stage{ position:static; width:auto; height:auto; transform:none!important; background:none; }
  .slide{ position:relative; display:block!important; visibility:visible!important; opacity:1!important; pointer-events:auto!important; width:1920px; height:1080px; break-after:page; page-break-after:always; }
  .slide:last-child{ break-after:auto; page-break-after:auto; }
  .deck-controls{ display:none!important; }
  .speaker-notes{ display:none!important; }
}
@media (prefers-reduced-motion:reduce){ *,*::before,*::after{ animation-duration:.01ms!important; transition-duration:.2s!important; } }

/* tokens — Corporate preset (Sora / DM Sans) */
:root{
  --font-display:'Sora',sans-serif; --font-body:'DM Sans',sans-serif;
  --stage-bg:#0b0f1a; --slide-bg:#ffffff;
  --ink:#0b0f1a; --ink-soft:#5b6478; --rule:#e6e9f0;
  --accent:#1f6feb; --accent-2:#0a7d55; --accent-warn:#b35900;
  --shadow:0 6px 24px rgba(11,15,26,.08);
}
*,*::before,*::after{ box-sizing:border-box; }
.slide{ font-family:var(--font-body); color:var(--ink); padding:84px 110px; }
.slide-number{ position:absolute; top:34px; right:54px; font-family:var(--font-body); font-size:14px; color:var(--ink-soft); letter-spacing:.08em; }
.slide-title{ font-family:var(--font-display); font-weight:700; font-size:58px; line-height:1.08; margin:0 0 14px; letter-spacing:-.01em; }
.headline{ font-family:var(--font-body); font-size:24px; line-height:1.45; color:var(--ink-soft); margin:0 0 30px; max-width:1500px; }
.kicker{ font-family:var(--font-body); font-size:15px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); margin:0 0 22px; }

/* reveal animations */
.reveal-left{ opacity:0; transform:translateX(-22px); animation:rvl .6s cubic-bezier(.2,.7,.2,1) forwards; }
.reveal-scale{ opacity:0; transform:scale(.96); animation:rvls .6s cubic-bezier(.2,.7,.2,1) forwards; }
.reveal{ opacity:0; animation:rvl .6s ease forwards; }
@keyframes rvl{ to{opacity:1;transform:none} }
@keyframes rvls{ to{opacity:1;transform:none} }
.delay-1{animation-delay:.08s}.delay-2{animation-delay:.16s}.delay-3{animation-delay:.24s}
.delay-4{animation-delay:.32s}.delay-5{animation-delay:.40s}.delay-6{animation-delay:.48s}

/* title slide */
.title-slide{ display:flex; flex-direction:column; justify-content:center; background:linear-gradient(135deg,#0b0f1a 0%,#13203a 60%,#1f3a5f 100%); color:#f4f7ff; }
.title-slide .slide-number{ color:rgba(255,255,255,.6); }
.title-stack{ max-width:1500px; }
.title-slide .kicker{ color:#6ea8fe; }
.title-slide h1{ font-family:var(--font-display); font-weight:700; font-size:76px; line-height:1.05; margin:0 0 24px; letter-spacing:-.015em; }
.title-slide .subtitle{ font-size:26px; line-height:1.5; color:#c4d0e8; margin:0; max-width:1200px; }
.hero-orb{ position:absolute; right:-120px; bottom:-160px; width:620px; height:620px; border-radius:50%; background:radial-gradient(circle at 35% 35%, rgba(110,168,254,.35), rgba(30,111,235,.05) 60%, transparent 70%); filter:blur(6px); }

/* split_text_visual */
.split-layout{ display:grid; grid-template-columns:1.05fr .95fr; gap:64px; align-items:center; height:100%; }
.bullet-list{ list-style:none; padding:0; margin:0; }
.bullet-list li{ font-size:23px; line-height:1.5; padding:12px 0 12px 30px; position:relative; color:var(--ink); }
.bullet-list li::before{ content:""; position:absolute; left:0; top:22px; width:10px; height:10px; border-radius:50%; background:var(--accent); }
.visual-panel{ background:linear-gradient(135deg,#f4f7ff,#eaf0fb); border:1px solid var(--rule); border-radius:20px; height:600px; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:48px; text-align:center; box-shadow:var(--shadow); }
.icon-lg{ width:150px; height:150px; color:var(--accent); }
.panel-caption{ margin-top:24px; font-size:20px; color:var(--ink-soft); max-width:460px; line-height:1.5; }

/* metric_dashboard */
.kpi-grid{ display:grid; grid-template-columns:repeat(var(--col-count,4),1fr); gap:28px; margin-top:30px; }
.kpi-card{ background:#fff; border:1px solid var(--rule); border-radius:18px; padding:34px 28px; box-shadow:var(--shadow); display:flex; flex-direction:column; justify-content:center; min-height:200px; }
.kpi-value{ font-family:var(--font-display); font-weight:700; font-size:54px; line-height:1; color:var(--accent); }
.kpi-label{ font-size:20px; color:var(--ink-soft); margin-top:14px; }

/* data_table */
.data-table{ width:100%; border-collapse:collapse; margin-top:30px; font-size:22px; }
.data-table th{ text-align:left; font-family:var(--font-display); font-weight:600; font-size:20px; color:#fff; background:var(--accent); padding:18px 26px; }
.data-table th:first-child{ border-radius:12px 0 0 0; }
.data-table th:last-child{ border-radius:0 12px 0 0; }
.data-table td{ padding:18px 26px; border-bottom:1px solid var(--rule); color:var(--ink); }
.data-table tbody tr:nth-child(even){ background:#f7f9fc; }

/* process_flow / timeline */
.process-flow{ display:grid; grid-template-columns:repeat(var(--step-count,4),1fr); gap:26px; margin-top:40px; }
.step-card{ background:#fff; border:1px solid var(--rule); border-radius:16px; padding:30px 24px; box-shadow:var(--shadow); position:relative; }
.step-number{ width:46px; height:46px; border-radius:50%; background:var(--accent); color:#fff; font-family:var(--font-display); font-weight:700; font-size:22px; display:flex; align-items:center; justify-content:center; margin-bottom:18px; }
.step-text{ font-size:20px; line-height:1.45; color:var(--ink); }

/* comparison_grid */
.comparison-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); gap:28px; margin-top:34px; }
.comparison-card{ background:#fff; border:1px solid var(--rule); border-left:6px solid var(--accent-warn); border-radius:14px; padding:26px 28px; box-shadow:var(--shadow); }
.comparison-card h3{ font-family:var(--font-display); font-size:22px; margin:0 0 10px; color:var(--accent-warn); }
.comparison-card p{ font-size:19px; line-height:1.5; color:var(--ink); margin:0; }
.comparison-card .ic{ display:inline-block; width:24px; height:24px; color:var(--accent-warn); vertical-align:middle; margin-right:8px; }

/* quote_card */
.quote-card{ display:flex; flex-direction:column; justify-content:center; height:100%; max-width:1500px; }
.quote-card blockquote{ font-family:var(--font-display); font-weight:600; font-size:40px; line-height:1.35; color:var(--ink); margin:0 0 36px; position:relative; padding-left:36px; border-left:6px solid var(--accent); }
.quote-card cite{ font-family:var(--font-body); font-style:normal; font-size:22px; color:var(--ink-soft); }

/* icon_grid */
.icon-grid{ display:grid; grid-template-columns:repeat(var(--col-count,3),1fr); gap:30px; margin-top:34px; }
.icon-card{ background:#fff; border:1px solid var(--rule); border-radius:16px; padding:32px 26px; text-align:center; box-shadow:var(--shadow); }
.icon-card .ic{ width:64px; height:64px; color:var(--accent); margin-bottom:16px; }
.icon-card h3{ font-family:var(--font-display); font-size:26px; margin:0 0 6px; color:var(--ink); }
.icon-card p{ font-size:18px; color:var(--ink-soft); margin:0; }

/* speaker notes overlay */
.speaker-notes{ display:none; }
body.show-notes .slide.active .speaker-notes{ display:block; position:fixed; left:50%; bottom:70px; transform:translateX(-50%); width:min(1200px,92vw); max-height:35vh; overflow:auto; background:rgba(10,15,26,.96); color:#e8edf7; padding:14px 18px; border-radius:10px; font-family:var(--font-body); font-size:14px; line-height:1.5; z-index:999; box-shadow:0 8px 30px rgba(0,0,0,.4); }
.notes-title{ font-weight:700; margin:0 0 8px; }
.notes-line{ margin:4px 0; }
.ev-ref{ color:#6ea8fe; font-weight:600; }
.badge-synth{ display:inline-block; background:#b35900; color:#fff; font-size:11px; padding:2px 8px; border-radius:4px; margin-top:6px; }
"""

# ---------- icon sprite ----------
SPRITE = """<svg style="display:none" aria-hidden="true">
<symbol id="ic-growth" viewBox="0 0 24 24"><path d="M3 17l6-6 4 4 8-9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 8h-5M21 8v5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" fill="none" stroke="currentColor" stroke-width="2"/></symbol>
<symbol id="ic-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 20c0-3.5 3-6 6-6s6 2.5 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="17" cy="9" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15 20c0-2.5 2-4.5 4-4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-dollar" viewBox="0 0 24 24"><path d="M12 3v18M16 7c0-2-2-3-4-3s-4 1-4 3 2 3 4 3 4 1 4 3-2 3-4 3-4-1-4-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-percent" viewBox="0 0 24 24"><path d="M5 19L19 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="7" cy="7" r="2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17" cy="17" r="2" fill="none" stroke="currentColor" stroke-width="2"/></symbol>
<symbol id="ic-warning" viewBox="0 0 24 24"><path d="M12 3l10 18H2L12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 10v5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-check" viewBox="0 0 24 24"><path d="M4 12l5 5L20 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="ic-flow" viewBox="0 0 24 24"><rect x="3" y="9" width="6" height="6" rx="1" fill="none" stroke="currentColor" stroke-width="2"/><rect x="15" y="9" width="6" height="6" rx="1" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 12h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-calendar" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 9h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-scale" viewBox="0 0 24 24"><path d="M12 3v18M7 21h10M5 7h14M9 7l-3 6h6l-3-6zM15 7l-3 6h6l-3-6z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="ic-building" viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 7h0M12 7h0M15 7h0M9 11h0M12 11h0M15 11h0M9 15h0M12 15h0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="ic-restaurant" viewBox="0 0 24 24"><path d="M7 3v8M7 3c-2 0-3 2-3 4s1 4 3 4M7 11v10M16 3c-2 0-2 4-2 6s0 4 2 4v8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="ic-travel" viewBox="0 0 24 24"><path d="M3 13l18-6-3 8-3-2-3 4-3-2-3 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></symbol>
<symbol id="ic-data" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 9h18M8 4v16" stroke="currentColor" stroke-width="2"/></symbol>
<symbol id="ic-quote" viewBox="0 0 24 24"><path d="M7 7c-2 1-3 3-3 6v4h6v-6H6c0-2 1-3 3-4zM18 7c-2 1-3 3-3 6v4h6v-6h-4c0-2 1-3 3-4z" fill="currentColor"/></symbol>
<symbol id="ic-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/></symbol>
<symbol id="ic-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" fill="none" stroke="currentColor" stroke-width="2"/><rect x="14" y="3" width="7" height="7" fill="none" stroke="currentColor" stroke-width="2"/><rect x="3" y="14" width="7" height="7" fill="none" stroke="currentColor" stroke-width="2"/><rect x="14" y="14" width="7" height="7" fill="none" stroke="currentColor" stroke-width="2"/></symbol>
<symbol id="ic-layers" viewBox="0 0 24 24"><path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 18l9 5 9-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></symbol>
<symbol id="ic-shield" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6l8-3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M9 12l2 2 4-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="ic-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7v5l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
</svg>"""

# ---------- icon inference ----------
ICON_BY_KEYWORD = [
    ("restaurant", "ic-restaurant"), ("dining", "ic-restaurant"), ("fork", "ic-restaurant"),
    ("travel", "ic-travel"), ("trip", "ic-travel"), ("europe", "ic-globe"), ("country", "ic-globe"), ("countries", "ic-globe"),
    ("revenue", "ic-dollar"), ("ebitda", "ic-dollar"), ("deal", "ic-dollar"), ("cash", "ic-dollar"), ("$700", "ic-dollar"),
    ("growth", "ic-growth"), ("+25", "ic-growth"), ("yoy", "ic-growth"),
    ("percent", "ic-percent"), ("%", "ic-percent"), ("margin", "ic-percent"),
    ("risk", "ic-warning"), ("consultation", "ic-warning"), ("regulatory", "ic-warning"), ("antitrust", "ic-shield"),
    ("leadership", "ic-users"), ("ceo", "ic-users"), ("advisor", "ic-users"),
    ("close", "ic-check"), ("timeline", "ic-calendar"), ("date", "ic-calendar"), ("founded", "ic-calendar"),
    ("flow", "ic-flow"), ("process", "ic-flow"), ("integration", "ic-flow"),
    ("network", "ic-grid"), ("venues", "ic-grid"), ("platform", "ic-layers"), ("bookings", "ic-restaurant"),
    ("quote", "ic-quote"), ("data", "ic-data"), ("scale", "ic-scale"),
]
def icon_for(text):
    t = (text or "").lower()
    for kw, ic in ICON_BY_KEYWORD:
        if kw in t:
            return ic
    return "ic-target"

# ---------- speaker notes ----------
def notes_block(sl, n):
    evs = sl.get("evidence_sources", [])
    sec = sl.get("section", "")
    grounding = (sl.get("speaker_notes") or sl.get("content", {}).get("headline") or sl.get("headline") or sl.get("title", "")).strip()
    grounding = strip_ids(grounding)
    # confidence: high unless any evidence is low/ocr or synthesized
    confs = [ev_conf(e["evidence_id"]) for e in evs if "evidence_id" in e]
    low = any(c in ("low", "medium") for c in confs)
    ocr = any("ocr" in (lk.get(e["evidence_id"], {}).get("extraction_method") or "") for e in evs if "evidence_id" in e)
    synth = "synth" in (sl.get("speaker_notes") or "").lower() or readiness < 60
    conf = "low" if (ocr or low) else "high"
    conf_reason = ""
    if ocr:
        conf_reason = " — OCR'd PDF source"
    elif low:
        conf_reason = " — medium-confidence source"
    if synth and readiness < 60:
        conf_reason += "; synthesized (readiness < 60)"
    lines = []
    lines.append(f'<p class="notes-title">SLIDE {n} — {esc(sl.get("title",""))}</p>')
    if sec:
        lines.append(f'<p class="notes-line"><strong>Section:</strong> {esc(sec)}</p>')
    if grounding:
        lines.append(f'<p class="notes-line"><strong>Grounding:</strong> {esc(grounding[:220])}</p>')
    if evs:
        ev_parts = []
        for e in evs[:6]:
            eid = e.get("evidence_id", "")
            sf = e.get("source_file") or ev_source(eid)
            what = ev_text(eid, 130)
            ev_parts.append(f'<span class="ev-ref">{esc(eid)}</span> {esc(sf)} — {esc(what)}')
        lines.append('<p class="notes-line"><strong>Evidence:</strong> ' + "; ".join(ev_parts) + '</p>')
    lines.append(f'<p class="notes-line"><strong>Confidence:</strong> {conf}{esc(conf_reason)}</p>')
    lines.append(f'<p class="notes-line"><strong>Synthesized:</strong> {"yes" if synth else "no"}</p>')
    if synth:
        lines.append('<span class="badge badge-synth">Synthesized</span>')
    return "\n  ".join(lines)

# ---------- renderers ----------
def render_title(sl, n):
    sub = sl.get("subtitle") or sl.get("headline") or P.get("audience", "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <div class="title-stack">
    <div class="kicker reveal-left delay-1">{esc(P.get("audience",""))}</div>
    <h1 class="reveal-left delay-2">{esc(sl["title"])}</h1>
    <p class="subtitle reveal-left delay-3">{esc(sub)}</p>
  </div>
  <div class="hero-orb reveal-scale delay-3" aria-hidden="true"></div>'''

def render_split(sl, n):
    c = sl.get("content", {})
    bullets = [strip_ids(b) for b in (c.get("bullets") or []) if strip_ids(b)]
    bullets = bullets[:6]
    pv = (sl.get("visual_spec") or sl.get("primary_visual") or {}).get("primary_visual", {})
    if not pv and "primary_visual" in sl:
        pv = sl.get("primary_visual", {})
    desc = strip_ids(pv.get("description", "")) or strip_ids(sl.get("headline", ""))
    ic = icon_for(sl.get("title","") + " " + (pv.get("type") or "") + " " + desc)
    bl = "\n      ".join(f'<li class="reveal-left delay-{min(i+4,6)}">{esc(b)}</li>' for i, b in enumerate(bullets))
    head = strip_ids(c.get("headline") or sl.get("headline") or "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <h2 class="slide-title reveal-left delay-2">{esc(sl["title"])}</h2>
  <p class="headline reveal-left delay-3">{esc(head)}</p>
  <div class="split-layout">
    <div class="text-column">
      <ul class="bullet-list">
      {bl}
      </ul>
    </div>
    <aside class="visual-panel reveal-scale delay-3">
      <svg class="icon-lg"><use href="#{ic}"/></svg>
      <p class="panel-caption">{esc(desc[:200])}</p>
    </aside>
  </div>'''

def render_metric(sl, n):
    c = sl.get("content", {})
    stats = c.get("key_stats") or []
    pv = (sl.get("visual_spec") or {}).get("primary_visual", {})
    if not stats:
        for s in (pv.get("steps_or_data") or []):
            if isinstance(s, str):
                parts = s.split(":", 1) if ":" in s else (s, "")
                stats.append({"label": strip_ids(parts[0]), "value": strip_ids(parts[1]) if len(parts) > 1 else ""})
    stats = stats[:6]
    cols = min(len(stats) if stats else 1, 6)
    cards = []
    for i, st in enumerate(stats[:6]):
        v = strip_ids(str(st.get("value", st if not isinstance(st, dict) else "")))
        l = strip_ids(str(st.get("label", "")))
        cards.append(f'<article class="kpi-card reveal-scale delay-{min(i+2,6)}"><div class="kpi-value">{esc(v)}</div><div class="kpi-label">{esc(l)}</div></article>')
    head = strip_ids(c.get("headline") or sl.get("headline") or "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <h2 class="slide-title reveal-left delay-2">{esc(sl["title"])}</h2>
  <p class="headline reveal-left delay-3">{esc(head)}</p>
  <div class="kpi-grid" style="--col-count:{cols}">
    {chr(10).join("    "+cd for cd in cards)}
  </div>'''

def render_data_table(sl, n):
    c = sl.get("content", {})
    pv = (sl.get("visual_spec") or {}).get("primary_visual", {})
    rows = pv.get("steps_or_data") or []
    # rows[0] is header; drop the Source column (last col if header[-1].lower()=="source")
    if not rows and c.get("key_stats"):
        rows = [["Metric", "Value", "Source"]] + [[s.get("label",""), s.get("value",""), s.get("source","")] for s in c["key_stats"]]
    header = rows[0] if rows else ["Metric", "Value"]
    drop_source = False
    if isinstance(header, list) and header and str(header[-1]).strip().lower() == "source":
        drop_source = True
    body_rows = rows[1:] if len(rows) > 1 else []
    def clean_row(r):
        cells = r if isinstance(r, list) else [r]
        if drop_source:
            cells = cells[:-1]
        return [strip_ids(str(x)) for x in cells]
    ths = "  <th>" + "</th>\n  <th>".join(esc(strip_ids(str(x))) for x in (header[:-1] if drop_source else header)) + "</th>"
    trs = []
    for i, r in enumerate(body_rows):
        cells = clean_row(r)
        tds = "<td>" + "</td>\n      <td>".join(esc(x) for x in cells) + "</td>"
        trs.append(f'    <tr class="reveal-left delay-{min(i+2,6)}">\n      {tds}\n    </tr>')
    head = strip_ids(c.get("headline") or sl.get("headline") or "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <h2 class="slide-title reveal-left delay-2">{esc(sl["title"])}</h2>
  <p class="headline reveal-left delay-3">{esc(head)}</p>
  <table class="data-table">
    <thead><tr>
  {ths}
    </tr></thead>
    <tbody>
{chr(10).join(trs)}
    </tbody>
  </table>'''

def render_process(sl, n):
    c = sl.get("content", {})
    pv = (sl.get("visual_spec") or {}).get("primary_visual", {})
    steps = pv.get("steps_or_data") or [strip_ids(b) for b in (c.get("bullets") or []) if strip_ids(b)]
    steps = [strip_ids(s) if isinstance(s, str) else strip_ids(s.get("label","") or s.get("text","")) for s in steps]
    steps = [s for s in steps if s][:6] or ["Step 1", "Step 2", "Step 3"]
    cards = []
    for i, s in enumerate(steps):
        cards.append(f'<article class="step-card reveal-scale delay-{min(i+2,6)}"><div class="step-number">{i+1}</div><div class="step-text">{esc(s)}</div></article>')
    head = strip_ids(c.get("headline") or sl.get("headline") or "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <h2 class="slide-title reveal-left delay-2">{esc(sl["title"])}</h2>
  <p class="headline reveal-left delay-3">{esc(head)}</p>
  <div class="process-flow" style="--step-count:{len(steps)}">
    {chr(10).join("    "+cd for cd in cards)}
  </div>'''

def render_comparison(sl, n):
    c = sl.get("content", {})
    pv = (sl.get("visual_spec") or {}).get("primary_visual", {})
    items = pv.get("steps_or_data") or [strip_ids(b) for b in (c.get("bullets") or []) if strip_ids(b)]
    cards = []
    for i, it in enumerate(items[:6]):
        it = strip_ids(it) if isinstance(it, str) else strip_ids(it.get("label","") or it.get("text",""))
        if isinstance(it, str) and ":" in it[:80]:
            h, b = it.split(":", 1)
        else:
            h, b = f"Point {i+1}", it
        cards.append(f'<article class="comparison-card reveal-scale delay-{min(i+2,6)}"><h3><svg class="ic"><use href="#ic-warning"/></svg>{esc(h.strip())}</h3><p>{esc(b.strip())}</p></article>')
    head = strip_ids(c.get("headline") or sl.get("headline") or "")
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <h2 class="slide-title reveal-left delay-2">{esc(sl["title"])}</h2>
  <p class="headline reveal-left delay-3">{esc(head)}</p>
  <div class="comparison-grid">
    {chr(10).join("    "+cd for cd in cards)}
  </div>'''

def render_quote(sl, n):
    pv = (sl.get("visual_spec") or sl.get("primary_visual") or {}).get("primary_visual", {})
    if not pv and "primary_visual" in sl:
        pv = sl.get("primary_visual", {})
    quotes = pv.get("steps_or_data") or []
    # pick the first quote
    q = ""
    cite = ""
    if quotes:
        q0 = quotes[0]
        if isinstance(q0, dict):
            q = q0.get("quote", "")
            cite = q0.get("attribution", "") or ""
        else:
            q = str(q0)
    if not q:
        q = sl.get("content", {}).get("body_text") or sl.get("headline") or sl.get("title", "")
    q = strip_ids(q)
    # cite from source_file of first evidence_source, not raw E####
    evs = sl.get("evidence_sources", [])
    if evs:
        cite = evs[0].get("source_file") or ev_source(evs[0].get("evidence_id", ""))
    # try to extract speaker name from the quote text itself (e.g. "..., said Rafa Marquez, President ...")
    m = re.search(r'said ([^.]+?),\s*(President|Chairman|CEO|Chief)', q)
    if m:
        cite = f"{m.group(1).strip()}, {m.group(2)}"
    elif m2 := re.search(r'said ([^.]+?)\.', q):
        cite = m2.group(1).strip()
    return f'''  <div class="slide-number">{n:02d} / {TOTAL:02d}</div>
  <div class="quote-card">
    <blockquote class="reveal-scale delay-2">“{esc(q)}”</blockquote>
    <cite class="reveal delay-3">{esc(cite)}</cite>
  </div>'''

RENDERERS = {
    "title_or_opening": render_title,
    "split_text_visual": render_split,
    "metric_dashboard": render_metric,
    "data_table": render_data_table,
    "full_process_flow": render_process,
    "timeline": render_process,
    "roadmap": render_process,
    "comparison_grid": render_comparison,
    "quote_card": render_quote,
    "icon_grid": render_split,  # icon_grid falls back to split with icon panel (no icon_grid in this deck)
    "other": render_split,
}

readiness = P.get("readiness_score", 0)
rc = P.get("readiness_components", {})
qf = P.get("quality_flags", [])

# ---------- build HTML ----------
sections = []
for i, sl in enumerate(slides):
    n = i + 1
    lay = sl["layout_type"]
    # force slide 1 to title
    if n == 1:
        lay = "title_or_opening"
    r = RENDERERS.get(lay, render_split)
    body = r(sl, n)
    notes = notes_block(sl, n)
    active = " active" if n == 1 else ""
    sections.append(f'''<section class="slide layout-{lay.replace('_','-')}{active}" data-slide-number="{n}">
  {body}
  <aside class="speaker-notes" data-slide-number="{n}">
  {notes}
  </aside>
</section>''')

DECK_JS = f'''<script>
(function () {{
  var stage = document.getElementById('stage');
  var viewport = document.getElementById('viewport');
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var counter = document.getElementById('counter');
  var prevBtn = document.getElementById('prevBtn');
  var nextBtn = document.getElementById('nextBtn');
  var notesBtn = document.getElementById('notesBtn');
  var current = 0;
  var total = slides.length;

  function fitStage() {{
    var vw = viewport.clientWidth || window.innerWidth;
    var vh = viewport.clientHeight || window.innerHeight;
    var scale = Math.min(vw / 1920, vh / 1080);
    var dx = (vw - 1920 * scale) / 2;
    var dy = (vh - 1080 * scale) / 2;
    stage.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(' + scale + ')';
  }}
  window.addEventListener('resize', fitStage);
  fitStage();

  function show(i) {{
    current = Math.max(0, Math.min(total - 1, i));
    for (var k = 0; k < total; k++) {{ slides[k].classList.toggle('active', k === current); }}
    if (counter) {{ counter.textContent = String(current + 1).padStart(2, '0') + ' / ' + String(total).padStart(2, '0'); }}
  }}
  function next() {{ show(current + 1); }}
  function prev() {{ show(current - 1); }}
  if (prevBtn) prevBtn.addEventListener('click', prev);
  if (nextBtn) nextBtn.addEventListener('click', next);
  if (notesBtn) notesBtn.addEventListener('click', function () {{ document.body.classList.toggle('show-notes'); }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{ e.preventDefault(); next(); }}
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{ e.preventDefault(); prev(); }}
    else if (e.key === 'Home') {{ show(0); }}
    else if (e.key === 'End') {{ show(total - 1); }}
    else if (e.key === 'n' || e.key === 'N') {{ document.body.classList.toggle('show-notes'); }}
  }});
  show(0);
  var DECK_META = {{ readiness_score: {readiness}, readiness_components: {json.dumps(rc)}, quality_flags: {json.dumps(qf)} }};
  window.DECK_META = DECK_META;
}})();
</script>'''

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(P["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
{SPRITE}
  <div class="deck-viewport" id="viewport">
    <div class="deck-stage" id="stage">
{chr(10).join(sections)}
    </div>
  </div>
  <div class="deck-controls">
    <button type="button" id="prevBtn" aria-label="Previous slide">‹</button>
    <span id="counter">01 / {TOTAL:02d}</span>
    <button type="button" id="nextBtn" aria-label="Next slide">›</button>
    <button type="button" id="notesBtn" aria-label="Toggle speaker notes">Notes</button>
  </div>
{DECK_JS}
</body>
</html>'''

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "presentation.html"), "w", encoding="utf-8").write(HTML)

# ---------- slide_notes.md ----------
md = [f"# Speaker Notes — {esc(P['title'])}\n"]
for i, sl in enumerate(slides):
    n = i + 1
    md.append(f"## Slide {n} — {strip_ids(sl.get('title',''))}\n")
    evs = sl.get("evidence_sources", [])
    md.append(f"**Section:** {sl.get('section','')}")
    g = strip_ids((sl.get("speaker_notes") or sl.get("content",{}).get("headline") or sl.get("headline") or sl.get("title","")))
    md.append(f"**Grounding:** {g[:220]}")
    if evs:
        parts = [f"`{e['evidence_id']}` {e.get('source_file') or ev_source(e['evidence_id'])} — {ev_text(e['evidence_id'],140)}" for e in evs[:6]]
        md.append("**Evidence:**\n" + "\n".join("- " + p for p in parts))
    confs = [ev_conf(e["evidence_id"]) for e in evs if "evidence_id" in e]
    ocr = any("ocr" in (lk.get(e["evidence_id"],{}).get("extraction_method") or "") for e in evs if "evidence_id" in e)
    conf = "low" if (ocr or any(c in ("low","medium") for c in confs)) else "high"
    synth = "yes" if (readiness < 60 or "synth" in (sl.get("speaker_notes") or "").lower()) else "no"
    md.append(f"**Confidence:** {conf}")
    md.append(f"**Synthesized:** {synth}\n")
open(os.path.join(OUT, "slide_notes.md"), "w", encoding="utf-8").write("\n".join(md))

# ---------- evidence_manifest.json ----------
manifest = {
    "source_handoff": "builder_handoff.json",
    "presentation_title": P["title"],
    "total_slides": TOTAL,
    "readiness_score": readiness,
    "readiness_components": rc,
    "quality_flags": qf,
    "slides": [],
}
for i, sl in enumerate(slides):
    n = i + 1
    evs = sl.get("evidence_sources", [])
    ids = [e["evidence_id"] for e in evs if "evidence_id" in e]
    ocr = any("ocr" in (lk.get(e["evidence_id"],{}).get("extraction_method") or "") for e in evs if "evidence_id" in e)
    confs = [ev_conf(e["evidence_id"]) for e in evs if "evidence_id" in e]
    conf = "low" if (ocr or any(c in ("low","medium") for c in confs)) else "high"
    synth = bool(readiness < 60 or "synth" in (sl.get("speaker_notes") or "").lower())
    manifest["slides"].append({
        "slide_number": n,
        "title": strip_ids(sl.get("title","")),
        "section": sl.get("section",""),
        "layout_type": "title_or_opening" if n == 1 else sl.get("layout_type",""),
        "evidence_ids": ids,
        "synthesized": synth,
        "confidence": conf,
    })
open(os.path.join(OUT, "evidence_manifest.json"), "w", encoding="utf-8").write(json.dumps(manifest, indent=2, ensure_ascii=False))

print("DONE. total slides:", TOTAL)
