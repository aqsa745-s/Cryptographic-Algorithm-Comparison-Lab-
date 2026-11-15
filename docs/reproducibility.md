# Reproducibility instructions

## Environment to record
Record the Windows version, CPU/processor, Python version, PyCryptodome version, pandas version, Streamlit version, and the date/time of the run. The supplied historical CSV summaries record PyCryptodome 4.4.0, but do not contain enough information to identify the original computer/OS. Do not guess missing environment details.

## Setup (Windows PowerShell, from project root)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
If script activation is blocked, use Command Prompt: `venv\Scripts\activate.bat`.

## Tests
```powershell
python -m pytest -q
```
Save the complete terminal output as evidence. The test suite checks round-trip correctness for empty/small/larger inputs, invalid inputs, metadata, frequency calculations, avalanche output bounds, and rejection of modified authentication tags by AES-GCM and ChaCha20-Poly1305.

## Run application
```powershell
streamlit run src/app.py
```
Select the same dataset files and algorithms, use at least 10 trials, click **Run experiments**, verify every `correct` value is True, and download raw and summary CSVs. Save screenshots of the app and results.

## Reproducibility rules
- Use identical input bytes and selected algorithms for a comparison.
- Record trial count and software/hardware environment.
- Keep raw trial rows; report median and range.
- Setup timing is recorded separately and excluded from operation-only timing.
- Timing will vary with CPU, OS, Python/library versions and background load.
- Never reuse an AES-GCM or ChaCha20-Poly1305 nonce with the same key. The benchmark generates a fresh random key and nonce/IV for each trial.
