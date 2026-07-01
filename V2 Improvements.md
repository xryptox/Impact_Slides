 ### Enhancement List: Deeper Insights from PPTX & Excel

 Here’s a structured list of meaningful enhancements, grouped by category:

 #### 1. PPTX – Deeper Slide & Content Analysis (Highest ROI)

 ┌─────┬──────────────────────────────────┬───────────────────────────────────────────────────────────────────────────┬────────────┬───────────┐
 │ #   │ Enhancement                      │ Description                                                               │ Difficulty │ Value     │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.1 │ Chart Data Extraction            │ Read actual series values and categories from charts (not just titles)    │ Medium     │ Very High │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.2 │ Table Cell Sampling              │ Extract top rows + key cells from tables (instead of just headers)        │ Easy       │ High      │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.3 │ Speaker Notes Extraction         │ Pull speaker notes and treat them as high-value evidence                  │ Easy       │ High      │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.4 │ Theme / Brand Color Detection    │ Detect dominant colors and fonts across the deck                          │ Medium     │ Medium    │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.5 │ Section / Master Slide Awareness │ Detect section breaks and slide layouts                                   │ Medium     │ Medium    │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.6 │ Text Hierarchy & Emphasis        │ Detect bold, large, or highlighted text as higher-priority insights       │ Easy       │ Medium    │
 ├─────┼──────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┼────────────┼───────────┤
 │ 1.7 │ Animation / Build Order          │ Detect if slides have heavy animation (indicator of narrative importance) │ Hard       │ Low       │
 └─────┴──────────────────────────────────┴───────────────────────────────────────────────────────────────────────────┴────────────┴───────────┘

 #### 2. Excel – Deeper Analytical Insights

 ┌─────┬───────────────────────────────┬───────────────────────────────────────────────────────────────┬────────────┬────────┐
 │ #   │ Enhancement                   │ Description                                                   │ Difficulty │ Value  │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.1 │ Trend / Time-series Detection │ Automatically detect date columns and calculate growth trends │ Medium     │ High   │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.2 │ Outlier & Anomaly Detection   │ Flag unusual values in numeric columns                        │ Medium     │ High   │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.3 │ Correlation Analysis          │ Suggest relationships between numeric columns                 │ Medium     │ High   │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.4 │ Pivot Table Detection         │ Identify and summarize pivot tables                           │ Hard       │ Medium │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.5 │ Formula vs Value Analysis     │ Detect calculated vs hardcoded values                         │ Medium     │ Medium │
 ├─────┼───────────────────────────────┼───────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 2.6 │ Sheet-level Summary Metrics   │ Generate sheet-level KPIs (total rows, null %, key columns)   │ Easy       │ Medium │
 └─────┴───────────────────────────────┴───────────────────────────────────────────────────────────────┴────────────┴────────┘

 #### 3. New File Format Support (User-requested)

 ┌─────┬─────────────────────────┬─────────────────────────────────────────────────────────────────────────────┬─────────────┬───────────┐
 │ #   │ Enhancement             │ Description                                                                 │ Difficulty  │ Value     │
 ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┼─────────────┼───────────┤
 │ 3.1 │ PDF Support             │ Extract text, tables, and structure from PDFs (using pymupdf or pdfplumber) │ Medium–High │ Very High │
 ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┼─────────────┼───────────┤
 │ 3.2 │ PDF Evidence Generation │ Create pdf_page_insight and pdf_table_insight evidence types                │ Medium      │ High      │
 ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┼─────────────┼───────────┤
 │ 3.3 │ DOCX Support            │ Extract headings, tables, and bullet lists from Word documents              │ Medium      │ High      │
 ├─────┼─────────────────────────┼─────────────────────────────────────────────────────────────────────────────┼─────────────┼───────────┤
 │ 3.4 │ Image & OCR Support     │ Run OCR on images embedded in PPTX/PDF and create image_ocr_insight         │ Hard        │ Medium    │
 └─────┴─────────────────────────┴─────────────────────────────────────────────────────────────────────────────┴─────────────┴───────────┘

 #### 4. Cross-cutting Improvements

 ┌─────┬──────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┬────────────┬────────┐
 │ #   │ Enhancement                      │ Description                                                                  │ Difficulty │ Value  │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.1 │ Evidence Confidence Scoring      │ Add a second dimension (confidence_score) alongside priority_score           │ Easy       │ High   │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.2 │ Evidence Deduplication           │ Merge very similar evidence entries across files                             │ Medium     │ Medium │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.3 │ Configurable Evidence Rules      │ Allow users to define custom rules (e.g., “boost anything with ‘recommend’”) │ Medium     │ High   │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.4 │ Multi-file Relationship Insights │ Detect when the same metric appears in both Excel and PPTX                   │ Hard       │ High   │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.5 │ Improved Console Logging         │ Add progress bars + per-file timing                                          │ Easy       │ Medium │
 ├─────┼──────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼────────────┼────────┤
 │ 4.6 │ Export to Markdown/CSV           │ Option to export Evidence Register in multiple formats                       │ Easy       │ Medium │
 └─────┴──────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┴────────────┴────────┘

 ────────────────────────────────────────────────────────────────────────────────

 ### Recommended Prioritization

 ┌─────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────┐
 │ Priority    │ Enhancements                                                                                         │ Rationale                            │
 ├─────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────┤
 │ High        │ PDF support (3.1 + 3.2), Chart data extraction (1.1), Speaker notes (1.3), Table cell sampling (1.2) │ Directly increases evidence richness │
 ├─────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────┤
 │ Medium-High │ Trend/outlier detection (2.1, 2.2), Brand/theme detection (1.4), DOCX support (3.3)                  │ Fills common gaps                    │
 ├─────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────┤
 │ Medium      │ Correlation analysis, Formula detection, Evidence deduplication                                      │ Nice analytical depth                │
 ├─────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────┤
 │ Future      │ OCR, Animation detection, Multi-file relationships                                                   │ Lower immediate value                │
 └─────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────┘

 ────────────────────────────────────────────────────────────────────────────────

 ### Final Recommendation

 Start with these top 5 enhancements:

 1. PDF Support (as you mentioned) — biggest scope expansion
 2. Chart Data Extraction from PPTX
 3. Speaker Notes Extraction
 4. Table Cell Sampling (actual data, not just headers)
 5. Time-series / Trend Detection in Excel

#### 4.3 Configurable Evidence Rules

 - Added boost_keywords parameter to the preprocessor
 - Users can now pass keywords via CLI:
   ```bash
     python step1_preprocessor_v2_full.py --input ... --output ... --boost-keywords recommend critical expand
   ```
 - Matching evidence receives a +0.15 priority boost (capped at 0.98)
 - Boosted entries are tagged with boosted_by_rule

 ────────────────────────────────────────────────────────────────────────────────

 ### Usage Example

 ```bash
   python step1_preprocessor_v2_full.py \
     --input ./materials \
     --output ./output \
     --filter-level moderate \
     --boost-keywords recommend critical growth
 ```

 This will:
 - Apply moderate filtering
 - Boost any evidence containing "recommend", "critical", or "growth"

  ### Summary

 #### 4.5 Improved Console Logging (Verbose Mode)

 - Added --verbose flag
 - When enabled:
     - Shows boost keywords and export settings
     - Prints per-file processing time
     - Shows total processing time at the end
     - Displays average time per file

 #### 4.6 Export to Markdown / CSV

 - Added --export-md and --export-csv flags
 - When enabled:
     - --export-md: Exports evidence_register.md (human-readable Markdown)
     - --export-csv: Exports evidence_register.csv (structured CSV)

 ### Usage Example

 ```bash
   python step1_preprocessor_v2_full.py \
     --input ./materials \
     --output ./output \
     --filter-level moderate \
     --boost-keywords recommend critical \
     --verbose \
     --export-md --export-csv
 ```