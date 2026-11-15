"""Cryptographic Algorithm Analysis and Comparison Lab.
Educational benchmarking only. DES is obsolete and must never protect real data.
"""
from __future__ import annotations
import os, platform, sys, time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
import pandas as pd
from Crypto.Cipher import AES, DES, ChaCha20_Poly1305
from Crypto.Util.Padding import pad, unpad

ALGORITHMS = ["DES-CBC (educational)", "AES-256-GCM", "ChaCha20-Poly1305"]
PARAMETERS = {
    "DES-CBC (educational)": {"mode": "CBC", "key_bits": 64, "nonce_or_iv_bytes": 8,
                              "authentication": "No (unauthenticated)", "library": "PyCryptodome"},
    "AES-256-GCM": {"mode": "GCM", "key_bits": 256, "nonce_or_iv_bytes": 12,
                    "authentication": "Yes (AEAD)", "library": "PyCryptodome"},
    "ChaCha20-Poly1305": {"mode": "Poly1305 AEAD", "key_bits": 256, "nonce_or_iv_bytes": 12,
                          "authentication": "Yes (AEAD)", "library": "PyCryptodome"},
}

def _now():
    return time.perf_counter_ns()

def encrypt_decrypt(algorithm: str, data: bytes):
    """Return package, recovered bytes and separate setup/operation timings in ms."""
    if not isinstance(data, bytes):
        raise TypeError("Input must be bytes.")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    if algorithm == "DES-CBC (educational)":
        t = _now()
        key, iv = os.urandom(8), os.urandom(8)
        enc_cipher = DES.new(key, DES.MODE_CBC, iv=iv)
        enc_setup = _now() - t
        padded = pad(data, 8)
        t = _now()
        ciphertext = enc_cipher.encrypt(padded)
        enc_op = _now() - t

        t = _now()
        dec_cipher = DES.new(key, DES.MODE_CBC, iv=iv)
        dec_setup = _now() - t
        t = _now()
        recovered = unpad(dec_cipher.decrypt(ciphertext), 8)
        dec_op = _now() - t
        package = iv + ciphertext
        return package, recovered, enc_setup/1e6, enc_op/1e6, dec_setup/1e6, dec_op/1e6, ciphertext

    if algorithm == "AES-256-GCM":
        t = _now()
        key, nonce = os.urandom(32), os.urandom(12)
        enc_cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        enc_setup = _now() - t
        t = _now()
        ciphertext, tag = enc_cipher.encrypt_and_digest(data)
        enc_op = _now() - t

        t = _now()
        dec_cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        dec_setup = _now() - t
        t = _now()
        recovered = dec_cipher.decrypt_and_verify(ciphertext, tag)
        dec_op = _now() - t
        return nonce + tag + ciphertext, recovered, enc_setup/1e6, enc_op/1e6, dec_setup/1e6, dec_op/1e6, ciphertext

    t = _now()
    key, nonce = os.urandom(32), os.urandom(12)
    enc_cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    enc_setup = _now() - t
    t = _now()
    ciphertext, tag = enc_cipher.encrypt_and_digest(data)
    enc_op = _now() - t

    t = _now()
    dec_cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    dec_setup = _now() - t
    t = _now()
    recovered = dec_cipher.decrypt_and_verify(ciphertext, tag)
    dec_op = _now() - t
    return nonce + tag + ciphertext, recovered, enc_setup/1e6, enc_op/1e6, dec_setup/1e6, dec_op/1e6, ciphertext

def benchmark(data: bytes, algorithms=None, trials=10, dataset_name="user_input"):
    if trials < 1:
        raise ValueError("Trials must be at least 1.")
    algorithms = ALGORITHMS if algorithms is None else algorithms
    if not algorithms:
        raise ValueError("Select at least one supported algorithm.")
    rows = []
    for alg in algorithms:
        if alg not in ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {alg}")
        for trial in range(1, trials + 1):
            package, recovered, es, enc, ds, dec, ciphertext = encrypt_decrypt(alg, data)
            p = PARAMETERS[alg]
            rows.append({
                "dataset": dataset_name, "algorithm": alg, "trial": trial,
                "input_bytes": len(data), "package_bytes": len(package),
                "ciphertext_bytes": len(ciphertext),
                "encryption_setup_ms": es, "encryption_ms": enc,
                "decryption_setup_ms": ds, "decryption_ms": dec,
                "encryption_total_ms": es + enc, "decryption_total_ms": ds + dec,
                "correct": recovered == data, "mode": p["mode"],
                "key_bits": p["key_bits"], "library": p["library"],
                "library_version": _package_version("pycryptodome"),
                "setup_in_operation_time": False,
            })
    return pd.DataFrame(rows)

def _package_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not detected"

def summarize_results(raw: pd.DataFrame):
    if raw.empty:
        return pd.DataFrame()
    keys = ["dataset", "algorithm", "input_bytes", "mode", "key_bits", "library", "library_version"]
    out = raw.groupby(keys, as_index=False).agg(
        trials=("trial", "count"),
        package_bytes_median=("package_bytes", "median"),
        encryption_median_ms=("encryption_ms", "median"),
        encryption_min_ms=("encryption_ms", "min"),
        encryption_max_ms=("encryption_ms", "max"),
        decryption_median_ms=("decryption_ms", "median"),
        decryption_min_ms=("decryption_ms", "min"),
        decryption_max_ms=("decryption_ms", "max"),
        encryption_setup_median_ms=("encryption_setup_ms", "median"),
        decryption_setup_median_ms=("decryption_setup_ms", "median"),
        all_correct=("correct", "all"),
    )
    out["encryption_range_ms"] = out["encryption_max_ms"] - out["encryption_min_ms"]
    out["decryption_range_ms"] = out["decryption_max_ms"] - out["decryption_min_ms"]
    return out

def bit_frequency(data: bytes):
    total = len(data) * 8
    ones = sum(x.bit_count() for x in data)
    return {"ones_fraction": ones/total if total else 0.0,
            "zeros_fraction": 1-ones/total if total else 0.0}

def byte_frequency(data: bytes):
    counts = [0]*256
    for b in data:
        counts[b] += 1
    return pd.DataFrame({"byte": list(range(256)), "count": counts})

def hamming_distance(a: bytes, b: bytes):
    if len(a) != len(b):
        raise ValueError("Inputs must have equal lengths.")
    return sum((x ^ y).bit_count() for x, y in zip(a, b))

def avalanche_demo(algorithm: str, data: bytes):
    """Controlled bit-flip observation. Fixed test parameters are never for real use."""
    if not data:
        raise ValueError("Provide at least one byte.")
    changed = bytes([data[0] ^ 1]) + data[1:]
    if algorithm == "DES-CBC (educational)":
        key, iv = bytes.fromhex("0123456789abcdef"), bytes.fromhex("1234567890abcdef")
        c1 = DES.new(key, DES.MODE_CBC, iv=iv).encrypt(pad(data, 8))
        c2 = DES.new(key, DES.MODE_CBC, iv=iv).encrypt(pad(changed, 8))
    elif algorithm == "AES-256-GCM":
        key, nonce = bytes(range(32)), bytes(range(12))
        c1, _ = AES.new(key, AES.MODE_GCM, nonce=nonce).encrypt_and_digest(data)
        c2, _ = AES.new(key, AES.MODE_GCM, nonce=nonce).encrypt_and_digest(changed)
    elif algorithm == "ChaCha20-Poly1305":
        key, nonce = bytes(range(32)), bytes(range(12))
        c1, _ = ChaCha20_Poly1305.new(key=key, nonce=nonce).encrypt_and_digest(data)
        c2, _ = ChaCha20_Poly1305.new(key=key, nonce=nonce).encrypt_and_digest(changed)
    else:
        raise ValueError("Unsupported algorithm.")
    diff = hamming_distance(c1, c2)
    total = len(c1)*8
    return {"algorithm": algorithm, "different_bits": diff, "compared_bits": total,
            "difference_fraction": diff/total}

def environment_info():
    return {"python_version": sys.version.split()[0], "platform": platform.platform(),
            "processor": platform.processor() or "Not reported",
            "pycryptodome": _package_version("pycryptodome"),
            "pandas": _package_version("pandas")}

def make_dataset(root="dataset"):
    """Create deterministic text and binary inputs: empty, 1KB, 10KB, 100KB."""
    root = Path(root)
    text_seed = ("Cryptography is the study of techniques for secure communication. "
                 "This is a reproducible educational benchmark dataset.\n").encode()
    binary_seed = bytes(range(256))
    specs = [("empty", 0), ("1KB", 1024), ("10KB", 10*1024), ("100KB", 100*1024)]
    manifest = []
    for kind, seed in [("text", text_seed), ("binary", binary_seed)]:
        folder = root/kind
        folder.mkdir(parents=True, exist_ok=True)
        for label, size in specs:
            data = (seed * ((size // max(len(seed),1))+1))[:size]
            path = folder/f"{kind}_{label}.bin" if kind == "binary" else folder/f"{kind}_{label}.txt"
            path.write_bytes(data)
            manifest.append({"dataset": path.name, "type": kind, "size_bytes": len(data)})
    return pd.DataFrame(manifest)
