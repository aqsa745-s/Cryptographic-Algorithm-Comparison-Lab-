# Final submission checklist — Artifact 5

## Included in this updated package
- [x] Python source code (`src/`) and Streamlit interface
- [x] README setup and execution instructions
- [x] Reproducible text and binary datasets with manifest
- [x] Supplied historical raw and summary CSV files (six runs; both 1 KB runs preserved)
- [x] Master results, comparison tables, parameter table and plots
- [x] Complete report in PDF and editable DOCX
- [x] Architecture flowchart (PNG) and architecture description (Markdown)
- [x] Automated test cases
- [x] Reproducibility instructions and test plan
- [x] Student-provided screenshot showing the fresh app experiment table and browser download prompts
- [x] Transcript of the fresh test result reported in chat: `21 passed in 2.39s`

## Final items to add from the student's own computer
- [ ] Add the actual downloaded `raw_results (6).csv` and `summary_results (6).csv` to `results/` (rename to `raw_results_fresh_2026-11-15.csv` and `summary_results_fresh_2026-11-15.csv`). The CSV contents were not attached with the ZIP, so they have not been fabricated or recreated.
- [ ] Add a screenshot of the PowerShell test output to `evidence/` if image evidence is required. The included TXT file is only a transcript of the output shared in chat.
- [ ] Add a clean screenshot of the app results (without the browser Downloads flyout) if desired.
- [ ] Record a short demo (about 1–2 minutes) and prepare an individual explanation of DES-CBC, AES-GCM, ChaCha20-Poly1305, median timing, and security limitations.
- [ ] Add student/registration/instructor details only if required by the instructor.

## Important interpretation notes
The historical report results and the new local run are separate datasets. Do not merge them unless the raw records and method are checked. The new screenshot shows the three algorithms selected, 10 trials, the raw-trial table and browser download prompts. It does not expose all downloaded CSV values. The reported test result is 21 passed in 2.39 seconds, based on the terminal output shared by the student; the TXT file is not a screenshot.
DES-CBC is obsolete and classroom-only. AES-GCM and ChaCha20-Poly1305 provide authenticated encryption, while DES-CBC does not. Performance measurements and statistical observations do not prove security.
