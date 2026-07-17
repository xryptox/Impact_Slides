Best Hybrid Workflow

 ### Step 1 — Python Preprocessor

 Generate clean intermediate files:

 ```text
   file_inventory.json
   extracted_documents.md
   excel_profile.json
   pptx_slide_audit.json
   brand_style_summary.json
   image_ocr_summary.json
   evidence_register_seed.json
   asset_manifest.json
 ```

 ### Step 2 — Impact Slide Analyst GPT

 Uses Python outputs instead of raw files to create:

 ```text
   Slide_Update_Plan.md
   Slide_Update_Plan.json
 ```

 ### Step 3 — Impact Slide Builder GPT

 Uses approved plan to create:

 ```text
   Final_Slide_Content.md
   Final_Slide_Content.json
 ```

 ### Step 4 — Python Builder / Validator

 Uses final JSON to:

 - validate schema
 - check missing evidence
 - check bullet length
 - check accessibility
 - create charts
 - generate PowerPoint

 Outputs:

 ```text
   final_validation_report.md
   updated_presentation.pptx
 ```

 Most Valuable Python Scripts to Build First

 1. File ingestion script
     - Detects all files and creates file_inventory.json.
 2. Excel profiler
     - Reads every sheet and creates sheet summaries, stats, trends, and cell references.
 3. PPTX analyzer
     - Extracts slide text, notes, layout, image count, chart data, font sizes, colors.
 4. Brand extractor
     - Pulls theme colors, fonts, logo placement, layout patterns.
 5. Evidence register generator
     - Creates source-backed evidence IDs before GPT reasoning.
 6. JSON validator
     - Ensures Analyst and Builder outputs follow schema.
 7. PPTX generator
     - Converts final approved JSON into actual slides.

 Recommended Tool Split

 Use Python for:

 │ extraction, measurement, validation, exact references, chart data, accessibility, PPT creation

 Use Custom GPTs for:

 │ interpretation, storyline, audience adaptation, slide messaging, persuasive structure, design direction

 This hybrid setup will be much more reliable than asking GPT-5.5 Instant to process everything directly.

Built the Step 1 Python Preprocessor script and saved it here:

 C:\Users\Ag1Le\Documents\impact_slide_preprocessor\step1_preprocessor.py

 I also ran a syntax check successfully.

 Run example

 ```bash
   python "C:\Users\Ag1Le\Documents\impact_slide_preprocessor\step1_preprocessor.py" --input "C:\path\to\your\source_files" --output "C:\path\to\output_folder" --ocr
 ```

 If you do not want OCR:

 ```bash
   python "C:\Users\Ag1Le\Documents\impact_slide_preprocessor\step1_preprocessor.py" --input "C:\path\to\your\source_files"
 ```

 Outputs created

 The script generates:

 - file_inventory.json
 - file_inventory.md
 - extracted_documents.md
 - excel_profile.json
 - pptx_slide_audit.json
 - brand_style_summary.json
 - image_ocr_summary.json
 - asset_manifest.json
 - evidence_register_seed.json
 - processing_errors.json
 - preprocessor_summary.md

 Start by opening:

 preprocessor_summary.md

 Then use those generated files with Impact Slide Analyst.

Step 2 = Use outputs with Impact Slide Analyst GPT

 After running step1_preprocessor.py, open the output folder. Start with:

 ```text
   preprocessor_summary.md
 ```

 Then upload/paste these files into your Impact Slide Analyst Custom GPT:

 ```text
   file_inventory.md
   extracted_documents.md
   excel_profile.json
   pptx_slide_audit.json
   brand_style_summary.json
   image_ocr_summary.json
   evidence_register_seed.json
   processing_errors.json
 ```

 Recommended prompt to Step 2 GPT

 Paste this into Impact Slide Analyst:

 ```text
   I ran the Python Step 1 preprocessor. Use the attached preprocessor outputs as your source of truth.

   Your task:
   1. Review the file inventory, extracted content, Excel profile, PPTX audit, brand summary, image OCR summary, and evidence register seed.
   2. Create the Alignment Summary.
   3. Ask the 5 alignment questions.
   4. Do not create final slide content yet.
   5. After I confirm alignment, create the Narrative Strategy, Existing Deck Audit if applicable, and Slide Update Plan.

   Treat evidence_register_seed.json as the starting evidence register. Preserve Evidence IDs where possible and add new IDs only if clearly supported by the preprocessor outputs.
 ```

 If files are too large

 Use this priority order:

 1. preprocessor_summary.md
 2. file_inventory.md
 3. evidence_register_seed.json
 4. pptx_slide_audit.json
 5. excel_profile.json
 6. brand_style_summary.json
 7. image_ocr_summary.json
 8. extracted_documents.md

 If extracted_documents.md is huge, paste only relevant sections/pages.

 Output you want from Step 2

 Ask Impact Slide Analyst to produce:

 ```text
   Slide_Update_Plan.md
 ```

 or, for handoff to Builder:

 ```text
   Slide_Update_Plan.json
 ```

 Then Step 3

 Use the approved Slide_Update_Plan.md/json with Impact Slide Builder GPT to generate final slide content and design specs.

 Step 3 = Use Impact Slide Builder GPT

 After Step 2, you should have an approved:

 ```text
   Slide_Update_Plan.md
 ```

 or

 ```text
   Slide_Update_Plan.json
 ```

 Upload/paste that file into Impact Slide Builder GPT.

 Prompt to use

 ```text
   Use this approved Slide Update Plan as your source of truth.

   Create final slide content and visual design specs for every planned slide.

   Rules:
   - Do not introduce claims not present in the Evidence Register.
   - Preserve Evidence IDs.
   - Follow the approved Why → What → How → Now structure.
   - Include slide purpose, headline, bullets, speaker notes, and visual design spec for each slide.
   - Keep bullets concise and presentation-ready.
 ```

 Expected output

 Impact Slide Builder should produce:

 ```text
   Final_Slide_Content.md
 ```

 or, if you ask for JSON:

 ```text
   Final_Slide_Content.json
 ```

 If you want JSON

 Use:

 ```text
   Export the final slide content as clean JSON using your final slide JSON schema. No Markdown, no extra commentary.
 ```

 Then Step 4

 Use Final_Slide_Content.json with Python Builder/Validator to validate and optionally generate a PowerPoint.