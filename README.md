# Cryptographic Algorithm Analysis and Comparison Lab


A reproducible educational application comparing:
- **DES-CBC** — historical/classroom comparison only; obsolete and insecure.
- **AES-256-GCM** — authenticated encryption (AEAD).
- **ChaCha20-Poly1305** — authenticated stream-cipher-based construction (AEAD).

## Features
- Streamlit interface for dataset selection or file upload.
- Reproducible text and binary inputs: empty, 1 KB, 10 KB and 100 KB.
- Repeated encryption/decryption trials using the same input bytes for each algorithm.
- Exact decryption correctness check.
- Input, ciphertext and stored-package sizes.
- Separate setup and cipher-operation timing; setup is excluded from operation columns.
- Median, minimum, maximum and range summaries.
- Raw and summary CSV export, saved under `results/`.
- Labeled median-time plots.
- Bit-frequency and byte-frequency observations.
- Controlled one-bit-flip avalanche observation.
- Parameter table, Python/library versions and automated tests.

## Windows setup (PowerShell)
Open PowerShell in this project folder and run:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

## Run the application
```powershell
streamlit run src/app.py
```
A local browser tab should open. Choose the built-in dataset, select the same files and algorithms, choose at least 10 trials, and click **Run experiments**.

## Run automated tests
```powershell
pytest -q
```

## Project structure
```text
Cryptographic_Algorithm_Comparison_Lab_Final/
├── dataset/
│   ├── text/                 # reproducible text samples
│   └── binary/               # reproducible binary samples
├── docs/
│   ├── architecture.md
│   ├── architecture_flowchart.png
│   ├── reproducibility.md
│   ├── parameter_table.md
│   └── test_plan_and_evidence.md
├── results/                  # supplied CSVs, graphs, and report
├── src/
│   ├── app.py                # Streamlit user interface
│   └── crypto_lab.py         # cipher and experiment logic
├── tests/
│   └── test_crypto_lab.py
├── report.pdf                # complete project report (PDF)
├── report.docx               # editable complete project report
├── requirements.txt
└── README.md
```

## Experimental method and timing policy
Every trial creates a fresh random key and IV/nonce. Setup time includes key/nonce generation and cipher-object initialization. The operation timing starts immediately before the encrypt/decrypt operation and excludes setup. Raw records contain setup, operation and combined total timings. All time values are milliseconds.

Run multiple trials and report the median and spread (range or IQR). Keep raw CSV records. Timing depends on CPU, operating system, Python, library version, background load, input size and implementation. Record the environment shown in the application.

## Interpretation and limitations
DES-CBC is unauthenticated and requires padding. AES-GCM and ChaCha20-Poly1305 provide authenticated encryption. Therefore, the comparison is not perfectly like-for-like: security properties and overhead differ. Describe the results as measurements of these implementations under your documented conditions, not a universal algorithm ranking.

Bit frequencies, byte frequencies and avalanche observations are optional descriptive experiments. They do not demonstrate resistance to cryptanalysis and are not security certificates. A single avalanche value depends on algorithm, mode, message and procedure.

## Security warnings
- DES is obsolete. Never use it for real or confidential information.
- Never reuse a nonce with the same key in AES-GCM or ChaCha20-Poly1305.
- The avalanche demonstration uses fixed parameters only to make a classroom experiment repeatable. Never copy those parameters into real encryption.
- Use only synthetic or authorized data.
- This is an educational prototype, not a production security product.

## Before submission
1. Run tests and save the terminal output/screenshot.
2. Run the app on your own computer.
3. Run the same dataset/algorithm/trial settings and save the generated CSVs.
4. Record the computer/software environment.
5. Insert your actual plots, CSV summary and screenshots into the report. Do not invent results.
6. Be ready to explain why DES is obsolete, why AEAD differs from CBC, what median/range mean, and why statistical observations do not prove security.

## Complete report and supporting documentation
- `report.pdf` and `report.docx` contain the complete project report.
- `results/parameter_table.csv` contains the algorithm parameter table.
- `docs/architecture_flowchart.png` contains the architecture flowchart.
- `docs/reproducibility.md` and `docs/test_plan_and_evidence.md` explain reproduction and evidence status.
- Historical result summaries are preserved; both 1 KB runs remain separate.
