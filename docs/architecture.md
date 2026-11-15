# System architecture and experiment flow

```text
             User / Researcher
                    |
                    v
           Streamlit User Interface
                    |
          Select dataset + algorithms
                    |
                    v
          Experiment Controller
                    |
          +---------+----------+
          |         |          |
          v         v          v
        DES-CBC   AES-GCM   ChaCha20-Poly1305
          |         |          |
          +---------+----------+
                    |
        Setup / Encrypt / Decrypt timers
                    |
                    v
          Exact plaintext comparison
                    |
          +---------+----------+
          |                    |
          v                    v
       Raw trial rows     Correctness result
          |
          v
    Median / min / max / range
          |
     +----+-----------+
     |                |
     v                v
  CSV exports     Labeled plots
```

## Data flow
1. The user chooses built-in text/binary data or uploads a file.
2. Each selected algorithm encrypts the same bytes for each trial.
3. Setup and operation durations are recorded separately.
4. The same trial key and nonce/IV are used only for that trial's matching decryption.
5. The recovered plaintext is compared byte-for-byte with the original.
6. Raw measurements are summarized and exported.
