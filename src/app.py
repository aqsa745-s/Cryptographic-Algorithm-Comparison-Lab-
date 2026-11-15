from pathlib import Path
import sys, io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crypto_lab import (ALGORITHMS, benchmark, summarize_results, bit_frequency,
                        byte_frequency, avalanche_demo, environment_info, make_dataset)

st.set_page_config(page_title="Crypto Analysis Lab", page_icon="🔐", layout="wide")
st.title("Cryptographic Algorithm Analysis & Comparison Lab")
st.caption("Educational research prototype | DES (historical), AES-256-GCM, ChaCha20-Poly1305")
st.warning("DES is obsolete and included only for classroom comparison. Never use DES to protect real data. This application is not a production security product.")

with st.sidebar:
    st.header("Experiment settings")
    algorithms = st.multiselect("Algorithms", ALGORITHMS, default=ALGORITHMS)
    trials = st.number_input("Trials per file and algorithm", min_value=3, max_value=100, value=10, step=1)
    st.caption("Use 10 or more trials for the course experiment; 20+ is preferable where practical.")

tab1, tab2, tab3, tab4 = st.tabs(["Benchmark", "Statistical observations", "Parameters & environment", "How to use"])

with tab1:
    st.subheader("Choose reproducible dataset or upload your own")
    choice = st.radio("Input source", ["Built-in reproducible dataset", "Upload one file"], horizontal=True)
    uploaded = None
    if choice == "Upload one file":
        uploaded = st.file_uploader("Choose a text or binary file", type=None)
        datasets = [(uploaded.name, uploaded.getvalue())] if uploaded else []
    else:
        if st.button("Create / refresh sample dataset"):
            manifest = make_dataset(ROOT/"dataset")
            st.success(f"Created {len(manifest)} reproducible text and binary samples.")
        dataset_files = sorted(list((ROOT/"dataset"/"text").glob("*")) + list((ROOT/"dataset"/"binary").glob("*")))
        if not dataset_files:
            make_dataset(ROOT/"dataset")
            dataset_files = sorted(list((ROOT/"dataset"/"text").glob("*")) + list((ROOT/"dataset"/"binary").glob("*")))
        selected_names = st.multiselect("Select input files", [p.name for p in dataset_files],
            default=[p.name for p in dataset_files if p.name in ["text_1KB.txt","binary_1KB.bin","text_10KB.txt","binary_10KB.bin"]])
        datasets = [(p.name, p.read_bytes()) for p in dataset_files if p.name in selected_names]

    st.info("Each selected input file is tested unchanged against each selected algorithm. Setup/key creation and cipher operation timings are recorded separately.")
    if st.button("Run experiments", type="primary", disabled=not algorithms or not datasets):
        frames = []
        progress = st.progress(0)
        total = len(datasets)
        for i, (name, data) in enumerate(datasets, 1):
            frames.append(benchmark(data, algorithms, int(trials), name))
            progress.progress(i/total)
        raw = pd.concat(frames, ignore_index=True)
        summary = summarize_results(raw)
        st.session_state["raw"] = raw
        st.session_state["summary"] = summary
        st.success("Experiment finished. Review correctness before interpreting timing.")

    if "raw" in st.session_state:
        raw, summary = st.session_state["raw"], st.session_state["summary"]
        st.subheader("Summary (median and range)")
        st.dataframe(summary, use_container_width=True)
        if raw["correct"].all():
            st.success("All tested decryptions recovered the exact original input.")
        else:
            st.error("At least one decryption correctness check failed. Do not use these results.")
        st.subheader("Median operation times")
        for metric, label in [("encryption_median_ms","Encryption"),("decryption_median_ms","Decryption")]:
            fig, ax = plt.subplots()
            for alg, part in summary.groupby("algorithm"):
                ax.plot(part["input_bytes"], part[metric], marker="o", label=alg)
            ax.set_xlabel("Input size (bytes)")
            ax.set_ylabel(f"Median {label.lower()} time (ms)")
            ax.set_title(f"Median {label} Time")
            ax.legend()
            ax.grid(True, alpha=.25)
            st.pyplot(fig)
            plt.close(fig)
        st.subheader("Raw trial records")
        st.dataframe(raw, use_container_width=True)
        st.download_button("Download raw_results.csv", raw.to_csv(index=False).encode(), "raw_results.csv", "text/csv")
        st.download_button("Download summary_results.csv", summary.to_csv(index=False).encode(), "summary_results.csv", "text/csv")
        raw.to_csv(ROOT/"results"/"raw_results.csv", index=False)
        summary.to_csv(ROOT/"results"/"summary_results.csv", index=False)
        st.caption("CSV copies are also saved in the project's results/ folder.")

with tab2:
    st.subheader("Bit and byte frequency")
    st.caption("These are descriptive observations, not cryptanalysis or proof of security.")
    stat_file = st.file_uploader("Upload a file for frequency analysis", key="stats_file")
    if stat_file:
        b = stat_file.getvalue()
        freq = bit_frequency(b)
        c1,c2,c3 = st.columns(3)
        c1.metric("Bytes", f"{len(b):,}")
        c2.metric("Bit ones", f"{freq['ones_fraction']:.4f}")
        c3.metric("Bit zeros", f"{freq['zeros_fraction']:.4f}")
        st.dataframe(byte_frequency(b), use_container_width=True, height=250)
        st.download_button("Download byte_frequency.csv", byte_frequency(b).to_csv(index=False).encode(),
                           "byte_frequency.csv", "text/csv")
    st.divider()
    st.subheader("One-bit-flip avalanche observation")
    avalanche_alg = st.selectbox("Algorithm", ALGORITHMS)
    avalanche_data = st.text_area("Short sample message", "Cryptography lab example")
    if st.button("Run avalanche observation"):
        result = avalanche_demo(avalanche_alg, avalanche_data.encode("utf-8"))
        st.json(result)
        st.warning("This is one controlled observation. Result depends on algorithm, mode, message and procedure; it is not a security certificate. Fixed test parameters are lab-only.")

with tab3:
    st.subheader("Documented comparison parameters")
    params = pd.DataFrame([
        {"Algorithm":a, "Mode":v["mode"], "Key bits":v["key_bits"],
         "IV/nonce bytes":v["nonce_or_iv_bytes"], "Authentication":v["authentication"],
         "Library":v["library"]} for a,v in __import__("crypto_lab").PARAMETERS.items()
    ])
    st.dataframe(params, use_container_width=True)
    st.caption("DES uses a 64-bit key representation with 56 effective key bits. AES and ChaCha use 256-bit keys. Nonces/IVs and authentication tags contribute to stored package size.")
    st.subheader("Current computer and library versions")
    st.json(environment_info())
    st.info("Timing policy: key/nonce generation and cipher-object initialization are recorded as setup time. Encryption/decryption operation columns exclude setup. Total time columns add the two. Python/library versions are captured in the raw CSV.")

with tab4:
    st.subheader("Reproducible workflow")
    st.markdown("""
1. Install dependencies from `requirements.txt`.
2. Create or refresh the included text and binary dataset.
3. Select the same files and algorithms for each run.
4. Use at least 10 trials (20+ recommended if practical).
5. Confirm every `correct` value is `True`.
6. Download raw and summary CSV files; keep them with your report.
7. Compare median values and range. Explain machine/software differences.
8. Do not claim that timing, entropy, frequency or avalanche observations prove security.
""")
    st.markdown("**Fairness limitation:** DES-CBC is unauthenticated and uses padding; AES-GCM and ChaCha20-Poly1305 are authenticated-encryption schemes. Their security properties are not identical, so speed results are implementation observations, not a universal ranking.")
    st.markdown("**Nonce rule:** Never reuse a nonce with the same key in AES-GCM or ChaCha20-Poly1305. This benchmark generates fresh random keys and nonces for every trial.")
