# Evidence Register - Q3 Business Review Test

**Total Entries:** 25  
**Generated:** Real-world mixed Excel + PPTX test (moderate filter)  
**Input Files:** `Q3_Sales_Data.xlsx` + `Q3_Business_Review.pptx`

## Evidence Entries

### E0020 — pptx_slide_insight (Priority: 0.98)
**Source:** Q3_Business_Review.pptx
**Text:** Q3_Business_Review.pptx - Slide 5: Key Recommendations (conclusion)
**Narrative Use:** ['What', 'How', 'Why']

### E0003 — numeric_range (Priority: 0.85)
**Source:** Q3_Sales_Data.xlsx
**Text:** Sheet1: 'Revenue' ranges from 650.0 to 1420.0.
**Narrative Use:** ['What', 'How']

### E0008 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • North region achieved record +23% YoY growth
**Narrative Use:** ['How', 'What']
**Metric:** +23% (percentage)

### E0009 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • Total revenue reached $4.8M (new high)
**Narrative Use:** ['How', 'What']
**Metric:** $4.8M (currency)

### E0010 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • East region underperformed at -4%
**Narrative Use:** ['How', 'What']
**Metric:** -4% (percentage)

### E0011 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • Enterprise segment grew 2.4x vs last year
**Narrative Use:** ['How', 'What']
**Metric:** 2.4x (multiplier)

### E0021 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • Expand North operations by 40%
**Narrative Use:** ['How', 'What']
**Metric:** 40% (percentage)

### E0012 — text_metric (Priority: 0.82)
**Source:** Q3_Business_Review.pptx
**Text:** • Expand North operations by 40% (percentage)
**Narrative Use:** ['How', 'What']

### E0022 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** Expand North operations by 40%
**Narrative Use:** ['What', 'Why']

### E0023 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** Invest in Enterprise segment (highest margin)
**Narrative Use:** ['What', 'Why']

### E0024 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** Review East region strategy
**Narrative Use:** ['What', 'Why']

### E0025 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** Target 15% overall growth in Q4
**Narrative Use:** ['What', 'Why']

### E0013 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** North region achieved record +23% YoY growth
**Narrative Use:** ['What', 'Why']

### E0014 — bullet_insight (Priority: 0.75)
**Source:** Q3_Business_Review.pptx
**Text:** Total revenue reached $4.8M (new high)
**Narrative Use:** ['What', 'Why']

### E0015 — categorical_distribution (Priority: 0.80)
**Source:** Q3_Sales_Data.xlsx
**Text:** Sheet1: 'Region' has 4 unique values. Top 3 account for 75.0% of records.
**Narrative Use:** ['Why', 'What']

### E0016 — categorical_distribution (Priority: 0.80)
**Source:** Q3_Sales_Data.xlsx
**Text:** Sheet1: 'Product' has 3 unique values. Top 3 account for 100.0% of records.
**Narrative Use:** ['Why', 'What']

### E0017 — categorical_distribution (Priority: 0.80)
**Source:** Q3_Sales_Data.xlsx
**Text:** Sheet1: 'Status' has 2 unique values. Top 3 account for 100.0% of records.
**Narrative Use:** ['Why', 'What']

### E0018 — categorical_distribution (Priority: 0.80)
**Source:** Q3_Sales_Data.xlsx
**Text:** Sheet1: 'Growth' has 21 unique values. Top 3 account for 20.8% of records.
**Narrative Use:** ['Why', 'What']

### E0019 — process_step (Priority: 0.76)
**Source:** Q3_Business_Review.pptx
**Text:** Lead Gen
**Narrative Use:** ['How', 'What']

### E0026 — process_step (Priority: 0.76)
**Source:** Q3_Business_Review.pptx
**Text:** Qualify
**Narrative Use:** ['How', 'What']

### E0027 — process_step (Priority: 0.76)
**Source:** Q3_Business_Review.pptx
**Text:** Proposal
**Narrative Use:** ['How', 'What']

### E0028 — process_step (Priority: 0.76)
**Source:** Q3_Business_Review.pptx
**Text:** Negotiation
**Narrative Use:** ['How', 'What']

### E0029 — process_step (Priority: 0.76)
**Source:** Q3_Business_Review.pptx
**Text:** Close
**Narrative Use:** ['How', 'What']

### E0030 — pptx_slide_insight (Priority: 0.60)
**Source:** Q3_Business_Review.pptx
**Text:** Q3_Business_Review.pptx - Slide 3: Revenue Performance (content_insight)
**Narrative Use:** ['What', 'Why']

### E0031 — pptx_slide_insight (Priority: 0.60)
**Source:** Q3_Business_Review.pptx
**Text:** Q3_Business_Review.pptx - Slide 4: Sales Process Flow (diagram_process)
**Narrative Use:** ['What', 'Why']

### E0032 — multi_column_suggestion (Priority: 0.65)
**Source:** Q3_Sales_Data.xlsx
**Text:** Consider analyzing numeric metrics grouped by categorical columns (e.g. Region vs Revenue).
**Narrative Use:** ['How', 'What']

---

**Summary**
- Highest priority evidence comes from the conclusion slide and strong numeric metrics.
- Process steps extracted from the diagram flow are cleanly captured as individual `process_step` entries.
- Text metrics include full context sentences, making them highly usable for narrative building.
- Evidence is well distributed between Excel findings and PPTX insights.