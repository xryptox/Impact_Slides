#!/usr/bin/env python3
"""Generate the Impact Slide Renderer output artifacts from builder_handoff.json."""
import json, html, os, re

BASE = r"C:/Users/Ag1Le/Documents/realworld_test/amex_thefork_acquisition"
HANDOFF = BASE + "/builder_handoff_detection/builder_handoff.json"
SEED = BASE + "/output_v4_detection_v2/evidence_register_seed.json"
OUT = BASE + "/renderer_handoff"
os.makedirs(OUT, exist_ok=True)

d = json.load(open(HANDOFF, encoding="utf-8"))
p = d["presentation"]
slides = d["slides"]
reg = json.load(open(SEED, encoding="utf-8"))
ev_by = {e.get("evidence_id"): e for e in reg}

def esc(s):
    return html.escape(str(s) if s is not None else "")

def clean_visible(s):
    """Strip E#### references from visible slide body text; IDs belong only in notes + data_table Source column."""
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"\s*\(\s*E\d{4}(?:\s*,\s*E\d{4})*\s*\)", "", s)  # '(E0159, E0164)'
    s = re.sub(r"\s*\[\s*E\d{4}(?:\s*,\s*E\d{4})*\s*\]", "", s)
    s = re.sub(r"\s*[,;]?\s*E\d{4}(?=\s|[,.;)\]!]|$)", "", s)  # bare trailing ' , E0164'
    s = re.sub(r"\(\s*,\s*", "(", s)   # '(,' -> '('
    s = re.sub(r"\(\s*\)", "", s)         # empty parens
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def ev_text(eid, maxlen=240):
    e = ev_by.get(eid)
    if not e:
        return "(evidence not found)"
    t = (e.get("text") or e.get("evidence_text") or e.get("content") or "").replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:maxlen] + ("…" if len(t) > maxlen else "")

def ev_src(eid):
    e = ev_by.get(eid)
    return e.get("source_file") if e else "?"

# ---- Build per-slide HTML ----
slide_html = []
notes_blocks = []
manifest_slides = []

SNUM = '<div class="slide-number">{:02d} / {}</div>'.format(0, len(slides))  # template reused per slide

def notes_block(s):
    """Build the hidden speaker-notes aside + the manifest entry + the md block."""
    n = len(slides)
    eid_list = [e["evidence_id"] for e in s.get("evidence_sources", [])]
    sn_builder = s.get("speaker_notes", "")
    synthesized = ("SYNTHESIZED" in sn_builder.upper()) or ("synthesized" in sn_builder.lower())
    # confidence: low for OCR'd PDFs or synthesized
    ocr = any(ev_by.get(eid, {}).get("ocr_used") for eid in eid_list)
    confidence = "low" if (ocr or synthesized) else "high"
    conf_reason = ""
    if ocr:
        conf_reason = " (OCR'd source page)"
    elif synthesized:
        conf_reason = " (synthesized; readiness < 60)"
    grounding = s.get("purpose") or s.get("audience_takeaway") or s.get("content", {}).get("headline", "")
    ev_lines = []
    for e in s.get("evidence_sources", []):
        eid = e["evidence_id"]
        ev_lines.append('<span class="ev-ref">{}</span> {} — {}'.format(
            esc(eid), esc(e.get("source_file") or ev_src(eid)), esc(ev_text(eid, 200))))
    ev_html = " ".join(ev_lines)
    badge = '<span class="badge badge-synth">Synthesized</span>' if synthesized else ""
    aside = (
        '<aside class="speaker-notes" data-slide-number="{n}">\n'
        '      <p class="notes-title">SLIDE {n} — {title}</p>\n'
        '      <p class="notes-line"><strong>Section:</strong> {section}</p>\n'
        '      <p class="notes-line"><strong>Grounding:</strong> {grounding}</p>\n'
        '      <p class="notes-line"><strong>Evidence:</strong> {ev}</p>\n'
        '      <p class="notes-line"><strong>Confidence:</strong> {conf}{reason}</p>\n'
        '      <p class="notes-line"><strong>Synthesized:</strong> {syn}</p>\n'
        '      {badge}\n'
        '    </aside>'
    ).format(
        n=s["slide_number"], title=esc(s["title"]), section=esc(s["section"]),
        grounding=esc(grounding), ev=ev_html,
        conf=confidence, reason=conf_reason,
        syn="yes" if synthesized else "no", badge=badge
    )
    # manifest entry
    manifest_slides.append({
        "slide_number": s["slide_number"],
        "title": s["title"],
        "section": s["section"],
        "layout_type": s["layout_type"],
        "evidence_ids": eid_list,
        "synthesized": synthesized,
        "confidence": confidence,
    })
    # md block
    md = [
        "## Slide {} — {}".format(s["slide_number"], s["title"]),
        "- **Section:** {}".format(s["section"]),
        "- **Grounding:** {}".format(grounding),
        "- **Evidence:**",
    ]
    for e in s.get("evidence_sources", []):
        eid = e["evidence_id"]
        md.append("  - `{}` {} — {}".format(eid, e.get("source_file") or ev_src(eid), ev_text(eid, 220)))
    md.append("- **Confidence:** {}{}".format(confidence, conf_reason))
    md.append("- **Synthesized:** {}".format("yes" if synthesized else "no"))
    md.append("")
    notes_blocks.append("\n".join(md))
    return aside

def section_header(s):
    c = s.get("content", {})
    return (
        '<div class="section-label reveal-left delay-1">{sec}</div>\n'
        '                <h2 class="slide-title reveal-left delay-2">{title}</h2>\n'
        '                <p class="headline reveal-left delay-3">{hl}</p>'
    ).format(sec=esc(s["section"]), title=esc(s["title"]),
            hl=esc(clean_visible(c.get("headline") or s.get("audience_takeaway") or "")))

def kpi_cards(s, cap=6):
    c = s.get("content", {})
    stats = c.get("key_stats") or []
    cards = []
    for i, st in enumerate(stats[:cap]):
        if isinstance(st, dict):
            val = st.get("value", "—")
            lbl = st.get("label", "")
        else:
            val, lbl = st, ""
        cards.append(
            '<article class="kpi-card reveal-scale delay-{d}">\n'
            '                            <div class="kpi-value">{v}</div>\n'
            '                            <div class="kpi-label">{l}</div>\n'
            '                        </article>'.format(d=min(i+2, 6), v=esc(val), l=esc(lbl))
        )
    col = len(stats[:cap]) if stats else 2
    return '<div class="kpi-grid" style="--col-count:{}">\n{}\n                </div>'.format(col, "\n".join(cards))

def data_table(s):
    vs = s.get("visual_spec", {}).get("primary_visual", {})
    rows = vs.get("steps_or_data") or []
    # rows[0] is header
    if not rows or not isinstance(rows[0], list):
        # fallback: build from key_stats
        c = s.get("content", {})
        ks = c.get("key_stats") or []
        header = ["Metric", "Value", "Source"]
        body = [[k.get("label", ""), k.get("value", ""), k.get("source", "")] for k in ks]
        rows = [header] + body
    header = rows[0]
    body = rows[1:]
    th = "".join("<th>{}</th>".format(esc(h)) for h in header)
    trs = []
    for i, r in enumerate(body):
        tds = "".join("<td>{}</td>".format(esc(str(c))) for c in r)
        trs.append('<tr class="reveal-left delay-{d}">{tds}</tr>'.format(d=min(i+2, 6), tds=tds))
    return (
        '<table class="data-table">\n'
        '  <thead><tr>{th}</tr></thead>\n'
        '  <tbody>\n    {trs}\n  </tbody>\n'
        '</table>'
    ).format(th=th, trs="\n    ".join(trs))

def process_flow(s, kind="process"):
    vs = s.get("visual_spec", {}).get("primary_visual", {})
    steps = vs.get("steps_or_data") or s.get("content", {}).get("bullets") or []
    steps = [str(x) for x in steps][:6] or ["Step 1", "Step 2", "Step 3"]
    cards = []
    for i, st in enumerate(steps):
        # strip trailing (E####) for the visible card text? No — keep it; it's reference, allowed in body text
        cards.append(
            '<article class="step-card reveal-scale delay-{d}">\n'
            '                            <div class="step-number">{n}</div>\n'
            '                            <div class="step-text">{t}</div>\n'
            '                        </article>'.format(d=min(i+2, 6), n=i+1, t=esc(clean_visible(st)))
        )
    cls = "timeline-flow" if kind == "timeline" else "process-flow"
    return '<div class="{cls}" style="--step-count:{n}">\n{c}\n                </div>'.format(
        cls=cls, n=len(steps), c="\n".join(cards))

def comparison_grid(s):
    vs = s.get("visual_spec", {}).get("primary_visual", {})
    items = vs.get("steps_or_data") or s.get("content", {}).get("bullets") or []
    items = [str(x) for x in items][:6] or ["Point 1", "Point 2"]
    cards = []
    for i, it in enumerate(items):
        if ":" in it[:80]:
            h, b = it.split(":", 1)
        else:
            h, b = "Point {}".format(i+1), it
        cards.append(
            '<article class="comparison-card reveal-scale delay-{d}">\n'
            '                            <svg class="icon icon-sm"><use href="#ic-warning"/></svg>\n'
            '                            <h3>{h}</h3>\n'
            '                            <p>{b}</p>\n'
            '                        </article>'.format(d=min(i+2, 6), h=esc(clean_visible(h.strip())), b=esc(clean_visible(b.strip())))
        )
    return '<div class="comparison-grid">\n{}\n                </div>'.format("\n".join(cards))

def split_layout(s, icon="ic-restaurant", panel_html=None):
    c = s.get("content", {})
    bullets = [b for b in (c.get("bullets") or []) if b][:6]
    bl = "\n".join(
        '<li class="reveal-left delay-{d}">{b}</li>'.format(d=min(i+4, 6), b=esc(clean_visible(b)))
        for i, b in enumerate(bullets)
    ) or '<li class="reveal-left delay-4">(no bullets — see headline)</li>'
    if panel_html is None:
        panel = '<svg class="icon icon-xl"><use href="#{}"/></svg>'.format(icon)
    else:
        panel = panel_html
    return (
        '                <div class="split-layout">\n'
        '                    <div class="text-column">\n'
        '                        {hdr}\n'
        '                        <ul class="bullet-list">\n{bl}\n                        </ul>\n'
        '                    </div>\n'
        '                    <aside class="visual-panel reveal-scale delay-3">\n'
        '                        {panel}\n'
        '                    </aside>\n'
        '                </div>'
    ).format(hdr=section_header(s), bl=bl, panel=panel)

# ---- render each slide ----
for s in slides:
    n = s["slide_number"]
    lay = s["layout_type"]
    active = " active" if n == 1 else ""
    snum = '<div class="slide-number">{:02d} / {:02d}</div>'.format(n, len(slides))
    aside = notes_block(s)

    if n == 1 or lay == "title_or_opening":
        # title slide (hard-coded for slide 1 even though Builder set quote_card)
        body = (
            '                <div class="title-stack">\n'
            '                    <div class="kicker reveal-left delay-1">Why · What · How · Now</div>\n'
            '                    <h1 class="reveal-left delay-2">{title}</h1>\n'
            '                    <p class="subtitle reveal-left delay-3">{sub}</p>\n'
            '                    <p class="audience reveal-left delay-4">Audience: {aud}</p>\n'
            '                    <p class="goal reveal-left delay-5">Goal: {goal}</p>\n'
            '                </div>\n'
            '                <div class="hero-orb reveal-scale delay-3" aria-hidden="true"></div>'
        ).format(
            title=esc(s["title"] or p["title"]),
            sub=esc(s.get("subtitle") or s.get("content", {}).get("headline") or p["subtitle"]),
            aud=esc(p["audience"]), goal=esc(p["primary_goal"]),
        )
        cls = "slide title-slide" + active
    elif lay == "metric_dashboard":
        body = section_header(s) + "\n                " + kpi_cards(s, cap=6)
        cls = "slide layout-metric-dashboard" + active
    elif lay == "data_table":
        body = section_header(s) + "\n                " + data_table(s)
        cls = "slide layout-data-table" + active
    elif lay in ("full_process_flow",):
        body = section_header(s) + "\n                " + process_flow(s, "process")
        cls = "slide layout-full-process-flow" + active
    elif lay in ("timeline", "roadmap"):
        body = section_header(s) + "\n                " + process_flow(s, "timeline")
        cls = "slide layout-" + lay + active
    elif lay == "comparison_grid":
        body = section_header(s) + "\n                " + comparison_grid(s)
        cls = "slide layout-comparison-grid" + active
    elif lay == "quote_card":
        c = s.get("content", {})
        quote = c.get("body_text") or c.get("headline") or s.get("title")
        # if body_text is placeholder, pull first quote from steps_or_data
        sod = s.get("visual_spec", {}).get("primary_visual", {}).get("steps_or_data") or []
        if (not quote or quote == "Executive voices on the strategic rationale.") and sod:
            quote = sod[0].get("quote", quote) if isinstance(sod[0], dict) else quote
        cite_src = ev_src(s["evidence_sources"][0]["evidence_id"]) if s.get("evidence_sources") else s.get("section", "")
        body = (
            '                <div class="quote-card">\n'
            '                    <svg class="icon icon-quote-mark" aria-hidden="true"><use href="#ic-quote"/></svg>\n'
            '                    <blockquote class="reveal-scale delay-2">{q}</blockquote>\n'
            '                    <cite class="reveal delay-3">{c}</cite>\n'
            '                </div>'
        ).format(q=esc(quote), c=esc(cite_src))
        cls = "slide layout-quote-card" + active
    else:  # split_text_visual, other
        # pick icon by section/semantic
        sem = s.get("_dominant_semantic_type") or ""
        icon = {"Metric": "ic-data", "Quote": "ic-quote", "Risk": "ic-warning"}.get(sem, "ic-restaurant")
        # slide 9 has table-shaped steps_or_data -> render a mini-table in panel
        sod = s.get("visual_spec", {}).get("primary_visual", {}).get("steps_or_data") or []
        panel_html = None
        if sod and isinstance(sod[0], list):
            # mini table in visual panel
            th = "".join("<th>{}</th>".format(esc(str(h))) for h in sod[0])
            trs = "".join("<tr>{}</tr>".format("".join("<td>{}</td>".format(esc(str(c))) for c in r)) for r in sod[1:])
            panel_html = '<table class="mini-table"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'.format(th=th, trs=trs)
        body = split_layout(s, icon=icon, panel_html=panel_html)
        cls = "slide layout-" + ("split-text-visual" if lay == "split_text_visual" else "other") + active

    sec = (
        '<section class="{cls}" data-slide-number="{n}">\n'
        '                {snum}\n'
        '{body}\n'
        '                {aside}\n'
        '            </section>'
    ).format(cls=cls, n=n, snum=snum, body=body, aside=aside)
    slide_html.append(sec)

SLIDES = "\n\n            ".join(slide_html)

# ---- SVG sprite ----
SPRITE = '''<svg style="display:none" aria-hidden="true">
  <symbol id="ic-growth" viewBox="0 0 24 24"><path d="M3 17l6-6 4 4 8-9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 8h-5M21 8v5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
  <symbol id="ic-decline" viewBox="0 0 24 24"><path d="M3 7l6 6 4-4 8 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
  <symbol id="ic-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" fill="none" stroke="currentColor" stroke-width="2"/></symbol>
  <symbol id="ic-users" viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 20c0-3.5 3-6 6-6s6 2.5 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="17" cy="9" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15 20c0-2.5 2-4.5 4-4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
  <symbol id="ic-dollar" viewBox="0 0 24 24"><path d="M12 3v18M16 7c0-2-2-3-4-3s-4 1-4 3 2 3 4 3 4 1 4 3-2 3-4 3-4-1-4-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
  <symbol id="ic-percent" viewBox="0 0 24 24"><path d="M5 19L19 5M8 7a2 2 0 11-4 0 2 2 0 014 0zM20 17a2 2 0 11-4 0 2 2 0 014 0z" fill="none" stroke="currentColor" stroke-width="2"/></symbol>
  <symbol id="ic-warning" viewBox="0 0 24 24"><path d="M12 3l10 18H2L12 3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M12 10v5M12 18v0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
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
</svg>'''

# ---- CSS ----
CSS = """
:root {
  --font-display: 'Sora', sans-serif;
  --font-body: 'DM Sans', sans-serif;
  --stage-bg: #0b0f1a;
  --slide-bg: #ffffff;
  --ink: #0b0f1a;
  --ink-soft: #5b6478;
  --accent: #1f6feb;
  --accent-2: #0a7d55;
  --accent-warn: #b35900;
  --line: #e3e7ef;
}
/* viewport-base.css (verbatim) */
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: var(--stage-bg, #0b0f1a); }
.deck-viewport { position: fixed; inset: 0; overflow: hidden; background: var(--stage-bg, #0b0f1a); }
.deck-stage { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; transform-origin: 0 0; background: var(--slide-bg, #fff); }
.slide { position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden; display: block; visibility: hidden; opacity: 0; pointer-events: none; background: var(--slide-bg, #fff); }
.slide.active, .slide.visible { visibility: visible; opacity: 1; pointer-events: auto; z-index: 1; }
img, video, canvas, svg { max-width: 100%; max-height: 100%; }
.deck-controls { position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%); z-index: 1000; }
@media print {
  html, body { width: 1920px; height: auto; overflow: visible; background: #fff; }
  .deck-viewport { position: static; overflow: visible; background: #fff; }
  .deck-stage { position: static; width: auto; height: auto; transform: none !important; background: none; }
  .slide { position: relative; display: block !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important; width: 1920px; height: 1080px; break-after: page; page-break-after: always; }
  .slide:last-child { break-after: auto; page-break-after: auto; }
  .deck-controls { display: none !important; }
  .speaker-notes { display: none !important; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.2s !important; } }

/* deck chrome */
body { font-family: var(--font-body); color: var(--ink); }
.deck-controls button { font: inherit; font-size: 18px; padding: 8px 14px; margin: 0 4px; border: 1px solid var(--line); background: #fff; color: var(--ink); border-radius: 8px; cursor: pointer; }
#counter { font-family: var(--font-display); font-weight: 600; padding: 0 10px; }
#notesBtn { font-weight: 600; }

/* slide base */
.slide { padding: 84px 96px; box-sizing: border-box; display: flex; flex-direction: column; }
.slide-number { position: absolute; top: 36px; right: 48px; font-family: var(--font-display); font-size: 20px; font-weight: 500; color: var(--ink-soft); letter-spacing: 0.04em; }
.section-label { font-family: var(--font-display); font-size: 20px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); margin-bottom: 14px; }
.slide-title { font-family: var(--font-display); font-size: 60px; font-weight: 700; line-height: 1.05; margin: 0 0 18px; color: var(--ink); }
.headline { font-size: 30px; line-height: 1.3; color: var(--ink-soft); margin: 0 0 36px; max-width: 1500px; }
.bullet-list { list-style: none; padding: 0; margin: 0; }
.bullet-list li { font-size: 26px; line-height: 1.4; padding: 10px 0 10px 34px; position: relative; }
.bullet-list li::before { content: ""; position: absolute; left: 0; top: 22px; width: 12px; height: 12px; background: var(--accent); border-radius: 2px; }

/* title slide */
.title-slide { justify-content: center; align-items: flex-start; background: linear-gradient(135deg, #0b0f1a 0%, #1a2a4a 60%, #0b0f1a 100%); color: #f4f7ff; }
.title-slide .slide-number { color: #8aa0c8; }
.title-slide .kicker { font-family: var(--font-display); font-size: 22px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent); margin-bottom: 28px; }
.title-slide h1 { font-family: var(--font-display); font-size: 78px; font-weight: 700; line-height: 1.02; margin: 0 0 22px; max-width: 1500px; }
.title-slide .subtitle { font-size: 30px; color: #c4d0e8; margin: 0 0 16px; max-width: 1300px; }
.title-slide .audience, .title-slide .goal { font-size: 20px; color: #8aa0c8; margin: 4px 0; }
.hero-orb { position: absolute; right: -120px; top: 50%; transform: translateY(-50%); width: 520px; height: 520px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, rgba(110,168,254,0.5), rgba(110,168,254,0) 70%); filter: blur(6px); }

/* split layout */
.split-layout { display: flex; gap: 64px; flex: 1; align-items: stretch; }
.split-layout .text-column { flex: 1.3; display: flex; flex-direction: column; }
.split-layout .visual-panel { flex: 1; background: linear-gradient(135deg, #f3f6fc 0%, #e6edf9 100%); border-radius: 20px; display: flex; align-items: center; justify-content: center; padding: 40px; border: 1px solid var(--line); }
.icon-xl { width: 200px; height: 200px; color: var(--accent); }
.icon-sm { width: 32px; height: 32px; color: var(--accent-warn); }

/* kpi grid */
.kpi-grid { display: grid; grid-template-columns: repeat(var(--col-count, 4), 1fr); gap: 28px; flex: 1; align-content: center; }
.kpi-card { background: linear-gradient(160deg, #f7f9fc 0%, #eef2f9 100%); border: 1px solid var(--line); border-left: 6px solid var(--accent); border-radius: 16px; padding: 36px 32px; display: flex; flex-direction: column; justify-content: center; }
.kpi-value { font-family: var(--font-display); font-size: 56px; font-weight: 700; line-height: 1; color: var(--ink); margin-bottom: 12px; }
.kpi-label { font-size: 22px; color: var(--ink-soft); }

/* data table */
.data-table { border-collapse: collapse; width: 100%; font-size: 26px; margin: 0; flex: 1; align-self: center; }
.data-table th { font-family: var(--font-display); text-align: left; padding: 18px 24px; background: #0b0f1a; color: #fff; font-weight: 600; font-size: 22px; letter-spacing: 0.04em; text-transform: uppercase; }
.data-table td { padding: 20px 24px; border-bottom: 1px solid var(--line); }
.data-table tr:nth-child(even) td { background: #f7f9fc; }
.data-table td:last-child { font-family: var(--font-display); color: var(--accent); font-weight: 600; }

/* mini table (in panel) */
.mini-table { border-collapse: collapse; width: 100%; font-size: 20px; }
.mini-table th { background: var(--accent); color: #fff; padding: 10px 14px; text-align: left; font-size: 18px; }
.mini-table td { padding: 10px 14px; border-bottom: 1px solid var(--line); background: #fff; }

/* process / timeline flow */
.process-flow, .timeline-flow { display: flex; gap: 24px; align-items: stretch; flex: 1; align-content: center; }
.timeline-flow { flex-direction: column; gap: 18px; max-width: 1500px; }
.step-card { flex: 1; background: #f7f9fc; border: 1px solid var(--line); border-top: 5px solid var(--accent); border-radius: 14px; padding: 28px 24px; display: flex; flex-direction: column; gap: 12px; }
.step-number { font-family: var(--font-display); font-size: 36px; font-weight: 700; color: var(--accent); }
.step-text { font-size: 24px; line-height: 1.35; }
.timeline-flow .step-card { flex-direction: row; align-items: center; gap: 24px; }
.timeline-flow .step-number { width: 56px; height: 56px; border-radius: 50%; background: var(--accent); color: #fff; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 26px; }

/* comparison grid */
.comparison-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; flex: 1; align-content: center; }
.comparison-card { background: #fff5ec; border: 1px solid #f0d8b8; border-left: 6px solid var(--accent-warn); border-radius: 14px; padding: 28px; display: flex; gap: 16px; align-items: flex-start; }
.comparison-card h3 { font-family: var(--font-display); font-size: 26px; margin: 0; color: var(--accent-warn); }
.comparison-card p { font-size: 22px; line-height: 1.35; margin: 0; color: var(--ink); }

/* quote card */
.layout-quote-card { justify-content: center; align-items: center; text-align: center; }
.quote-card { max-width: 1400px; position: relative; }
.icon-quote-mark { width: 64px; height: 64px; color: var(--accent); margin: 0 auto 20px; display: block; }
.quote-card blockquote { font-family: var(--font-display); font-size: 40px; font-weight: 600; line-height: 1.3; margin: 0 0 28px; color: var(--ink); }
.quote-card cite { font-size: 24px; color: var(--ink-soft); font-style: normal; }

/* speaker notes (hidden) */
.speaker-notes { display: none; position: absolute; left: 96px; right: 96px; bottom: 60px; top: auto; background: #0b0f1a; color: #e4e9f2; border-radius: 12px; padding: 24px 32px; font-size: 18px; line-height: 1.5; max-height: 420px; overflow: auto; border: 1px solid #2a3450; }
body.show-notes .speaker-notes { display: block; }
.speaker-notes .notes-title { font-family: var(--font-display); font-weight: 700; font-size: 20px; margin: 0 0 12px; color: #fff; }
.speaker-notes .notes-line { margin: 6px 0; }
.speaker-notes .ev-ref { font-family: var(--font-display); font-weight: 600; color: var(--accent); background: #162十三ab; padding: 1px 6px; border-radius: 4px; }
.speaker-notes .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 14px; font-weight: 700; margin-top: 8px; }
.badge-synth { background: var(--accent-warn); color: #fff; }

/* reveal animations */
@keyframes rev { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
@keyframes revscale { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: none; } }
.reveal, .reveal-left { animation: rev 0.7s ease both; }
.reveal-scale { animation: revscale 0.7s ease both; }
.delay-1 { animation-delay: 0.05s; }
.delay-2 { animation-delay: 0.15s; }
.delay-3 { animation-delay: 0.25s; }
.delay-4 { animation-delay: 0.35s; }
.delay-5 { animation-delay: 0.45s; }
.delay-6 { animation-delay: 0.55s; }
"""

# fix the typo I introduced (garbled char in ev-ref background)
CSS = CSS.replace("background: #162十三ab;", "background: #16213ab;")

# ---- JS ----
rc = json.dumps(p.get("readiness_components", {}))
qf = json.dumps(p.get("quality_flags", []))
JS = """
const DECK_META = {
  readiness_score: %d,
  readiness_components: %s,
  quality_flags: %s,
  framework: %s,
  total_slides: %d
};
const stage = document.getElementById('stage');
const slides = Array.from(document.querySelectorAll('.slide'));
const counter = document.getElementById('counter');
let current = 0;
function fitStage() {
  const vw = window.innerWidth, vh = window.innerHeight;
  const s = Math.min(vw / 1920, vh / 1080);
  const x = (vw - 1920 * s) / 2, y = (vh - 1080 * s) / 2;
  stage.style.transform = `translate(${{x}}px, ${{y}}px) scale(${{s}})`;
}
function show(i) {
  slides.forEach((sl, idx) => sl.classList.toggle('active', idx === i));
  counter.textContent = `${{String(i+1).padStart(2,'0')}} / ${{String(slides.length).padStart(2,'0')}}`;
  current = i;
}
window.addEventListener('resize', fitStage);
document.getElementById('prevBtn').addEventListener('click', () => show(Math.max(0, current-1)));
document.getElementById('nextBtn').addEventListener('click', () => show(Math.min(slides.length-1, current+1)));
document.getElementById('notesBtn').addEventListener('click', () => document.body.classList.toggle('show-notes'));
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') show(Math.min(slides.length-1, current+1));
  if (e.key === 'ArrowLeft') show(Math.max(0, current-1));
  if (e.key === 'n' || e.key === 'N') document.body.classList.toggle('show-notes');
});
fitStage();
show(0);
""" % (p["readiness_score"], rc, qf, json.dumps(p.get("framework")), len(slides))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
{sprite}
<div class="deck-viewport" id="viewport">
  <div class="deck-stage" id="stage">
            {slides}
  </div>
</div>
<div class="deck-controls">
  <button id="prevBtn" aria-label="Previous">&#8249;</button>
  <span id="counter">01 / 14</span>
  <button id="nextBtn" aria-label="Next">&#8250;</button>
  <button id="notesBtn" aria-label="Toggle speaker notes">Notes</button>
</div>
<script>
{js}
</script>
</body>
</html>""".format(
    title=esc(p["title"]), css=CSS, sprite=SPRITE, slides=SLIDES, js=JS
)

html_path = OUT + "/presentation.html"
open(html_path, "w", encoding="utf-8").write(HTML)

# ---- slide_notes.md ----
md = [
    "# Speaker Notes — AmEx Acquires TheFork",
    "",
    "Deck: **{}**".format(p["title"]),
    "Narrative Readiness Score: **{}/100** (low — evidence limitations flagged; Strategic Context rule #4 active)".format(p["readiness_score"]),
    "Quality flags: {}".format(", ".join(p["quality_flags"])),
    "",
    "Source handoff: `builder_handoff_detection/builder_handoff.json` (14 slides).",
    "Evidence source of truth: `output_v4_detection_v2/evidence_register_seed.json` (124 entries).",
    "",
]
md.extend(notes_blocks)
open(OUT + "/slide_notes.md", "w", encoding="utf-8").write("\n".join(md))

# ---- evidence_manifest.json ----
manifest = {
    "source_handoff": "builder_handoff_detection/builder_handoff.json",
    "evidence_source": "output_v4_detection_v2/evidence_register_seed.json",
    "presentation_title": p["title"],
    "total_slides": len(slides),
    "readiness_score": p["readiness_score"],
    "readiness_components": p["readiness_components"],
    "quality_flags": p["quality_flags"],
    "slides": manifest_slides,
}
with open(OUT + "/evidence_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

# ---- validation ----
print("=== VALIDATION ===")
print("HTML bytes:", os.path.getsize(html_path))
print("slides in HTML:", HTML.count('<section class="slide'))
print("notes asides in HTML:", HTML.count('class="speaker-notes"'))
print("symbol count:", HTML.count('<symbol id="ic-'))
# on-slide E#### outside of td/aside
import re
# count E#### occurrences total
e_total = len(re.findall(r'E\d{4}', HTML))
e_in_td = len(re.findall(r'<td>E\d{4}</td>', HTML))
e_in_aside = len(re.findall(r'<aside class="speaker-notes"[^>]*>.*?</aside>', HTML, re.DOTALL))
e_in_aside_ids = sum(len(re.findall(r'E\d{4}', m)) for m in re.findall(r'<aside class="speaker-notes"[^>]*>.*?</aside>', HTML, re.DOTALL))
print("E#### total:", e_total, "| in <td>:", e_in_td, "| inside asides:", e_in_aside_ids)
print("visible-on-slide E#### (should be td only):", e_total - e_in_td - e_in_aside_ids)
# manifest validity
json.load(open(OUT + "/evidence_manifest.json", encoding="utf-8"))
print("manifest valid JSON: OK")
# cross-check evidence IDs
seed_ids = set(ev_by.keys())
man_ids = set()
for s in manifest_slides:
    for eid in s["evidence_ids"]:
        man_ids.add(eid)
missing = [i for i in man_ids if i not in seed_ids]
print("manifest evidence IDs:", len(man_ids), "| missing from seed:", len(missing), missing)
# count evidence IDs in HTML notes vs manifest
html_note_ids = set(re.findall(r'E\d{4}', "\n".join(re.findall(r'<aside class="speaker-notes"[^>]*>.*?</aside>', HTML, re.DOTALL))))
print("evidence IDs in HTML notes:", len(html_note_ids))
print("DONE")
