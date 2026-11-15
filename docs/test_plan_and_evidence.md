# Test plan and evidence

| Test | Expected result | Evidence available in package |
|---|---|---|
| Valid round trip for DES-CBC, AES-GCM and ChaCha20-Poly1305 | Recovered bytes exactly equal input | Supplied experiment summaries report `all_correct=True` for all 18 algorithm-summary records; automated test is included |
| Empty, one-byte, short and larger input | Supported algorithms complete round trip | Automated parameterized tests included |
| Invalid input type / unknown algorithm / zero trials / empty algorithm list | Clear TypeError or ValueError | Automated tests included |
| AEAD authentication tag modified | AES-GCM and ChaCha20-Poly1305 reject the message | Automated test included |
| Summary metadata and timing spread | Required columns present; range non-negative | Automated test included |
| Bit/byte frequency and avalanche helper | Valid output in expected numeric range | Automated tests included |

## Execution status
The source package includes the test suite, but no fresh test-run screenshot or terminal log is claimed in this generated package. Run `python -m pytest -q` on the target Windows computer and save its actual output. Historical experiment CSV summaries independently record 18 `all_correct=True` algorithm-summary entries; this is not a substitute for a fresh automated test run.
