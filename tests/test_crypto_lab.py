import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from Crypto.Cipher import AES, ChaCha20_Poly1305
from crypto_lab import (
    ALGORITHMS, PARAMETERS, encrypt_decrypt, benchmark, summarize_results,
    hamming_distance, bit_frequency, byte_frequency, avalanche_demo,
)

@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize("data", [b"", b"x", b"hello world", bytes(range(256)) * 5])
def test_round_trip(algorithm, data):
    package, recovered, es, enc, ds, dec, ciphertext = encrypt_decrypt(algorithm, data)
    assert isinstance(package, bytes)
    assert recovered == data
    assert min(es, enc, ds, dec) >= 0
    assert len(ciphertext) >= len(data)
    assert len(package) >= len(ciphertext)


def test_benchmark_and_metadata():
    raw = benchmark(b"test" * 100, ALGORITHMS, 3, "fixture")
    summary = summarize_results(raw)
    assert len(raw) == 9
    assert raw["correct"].all()
    assert raw["setup_in_operation_time"].eq(False).all()
    assert raw["library_version"].notna().all()
    assert raw["mode"].notna().all()
    assert raw["key_bits"].notna().all()
    assert len(summary) == 3
    assert summary["all_correct"].all()
    assert (summary["encryption_range_ms"] >= 0).all()
    assert (summary["decryption_range_ms"] >= 0).all()


def test_invalid_inputs_and_parameters():
    with pytest.raises(TypeError):
        encrypt_decrypt(ALGORITHMS[0], "not bytes")
    with pytest.raises(ValueError):
        benchmark(b"x", ALGORITHMS, 0)
    with pytest.raises(ValueError):
        benchmark(b"x", [], 3)
    with pytest.raises(ValueError):
        encrypt_decrypt("unknown", b"x")
    with pytest.raises(ValueError):
        avalanche_demo("unknown", b"x")


def test_aead_rejects_modified_authentication_tag():
    # Verify the maintained library rejects tampered tags for both AEAD options.
    data = b"authenticated test message"
    key, nonce = bytes(range(32)), bytes(range(12))

    aes = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = aes.encrypt_and_digest(data)
    bad_tag = bytes([tag[0] ^ 1]) + tag[1:]
    dec = AES.new(key, AES.MODE_GCM, nonce=nonce)
    with pytest.raises(ValueError):
        dec.decrypt_and_verify(ciphertext, bad_tag)

    chacha = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    ciphertext, tag = chacha.encrypt_and_digest(data)
    bad_tag = bytes([tag[0] ^ 1]) + tag[1:]
    dec = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    with pytest.raises(ValueError):
        dec.decrypt_and_verify(ciphertext, bad_tag)


def test_hamming_distance():
    assert hamming_distance(b"\x00", b"\x01") == 1
    with pytest.raises(ValueError):
        hamming_distance(b"a", b"ab")


def test_frequency():
    f = bit_frequency(bytes([0, 255]))
    assert f["ones_fraction"] == .5
    assert f["zeros_fraction"] == .5
    assert byte_frequency(bytes([0, 255]))["count"].sum() == 2


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_avalanche(algorithm):
    result = avalanche_demo(algorithm, b"hello world")
    assert result["compared_bits"] > 0
    assert 0 <= result["difference_fraction"] <= 1


def test_parameter_table_is_complete():
    assert set(PARAMETERS) == set(ALGORITHMS)
    for values in PARAMETERS.values():
        assert values["mode"]
        assert values["key_bits"] > 0
        assert values["nonce_or_iv_bytes"] > 0
        assert values["library"] == "PyCryptodome"
