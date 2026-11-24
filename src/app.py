"""Flask web interface for the Cryptographic Algorithm Comparison Lab.

Vercel looks for a top-level `app` variable in src/app.py.
Educational benchmarking only. DES is obsolete and must never protect real data.
"""
import json
import sys
from pathlib import Path

from flask import Flask, Response, jsonify, request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crypto_lab import (  # noqa: E402
    ALGORITHMS, PARAMETERS, avalanche_demo, benchmark, bit_frequency,
    byte_frequency, environment_info, summarize_results,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # Vercel request limit is about 4.5 MB

MAX_TRIALS = 30  # keeps one request inside Vercel's function time limit

TEXT_SEED = (
    b"Cryptography is the study of techniques for secure communication. "
    b"This is a reproducible educational benchmark dataset.\n"
)
BINARY_SEED = bytes(range(256))
SIZES = {"empty": 0, "1KB": 1024, "10KB": 10 * 1024, "100KB": 100 * 1024}


def sample_files():
    """Deterministic in-memory samples (Vercel's disk is read-only, so nothing is written)."""
    files = {}
    for kind, seed, ext in [("text", TEXT_SEED, "txt"), ("binary", BINARY_SEED, "bin")]:
        for label, size in SIZES.items():
            data = (seed * (size // len(seed) + 1))[:size]
            files[f"{kind}_{label}.{ext}"] = data
    return files


SAMPLES = sample_files()


def df_to_records(df):
    return json.loads(df.to_json(orient="records"))


@app.get("/api/info")
def api_info():
    params = [
        {
            "Algorithm": name,
            "Mode": p["mode"],
            "Key bits": p["key_bits"],
            "IV/nonce bytes": p["nonce_or_iv_bytes"],
            "Authentication": p["authentication"],
            "Library": p["library"],
        }
        for name, p in PARAMETERS.items()
    ]
    return jsonify(
        algorithms=ALGORITHMS,
        samples=list(SAMPLES.keys()),
        default_samples=["text_1KB.txt", "binary_1KB.bin", "text_10KB.txt", "binary_10KB.bin"],
        params=params,
        environment=environment_info(),
        max_trials=MAX_TRIALS,
    )


@app.post("/api/benchmark")
def api_benchmark():
    algs = [a for a in request.form.getlist("algorithms") if a in ALGORITHMS]
    if not algs:
        return jsonify(error="Select at least one algorithm."), 400
    try:
        trials = int(request.form.get("trials", 10))
    except ValueError:
        return jsonify(error="Trials must be a number."), 400
    trials = max(3, min(trials, MAX_TRIALS))

    datasets = []
    upload = request.files.get("file")
    if upload and upload.filename:
        datasets.append((upload.filename, upload.read()))
    else:
        for name in request.form.getlist("samples"):
            if name in SAMPLES:
                datasets.append((name, SAMPLES[name]))
    if not datasets:
        return jsonify(error="Select at least one sample file or upload a file."), 400

    import pandas as pd

    raw = pd.concat([benchmark(data, algs, trials, name) for name, data in datasets], ignore_index=True)
    summary = summarize_results(raw)
    return jsonify(
        raw=df_to_records(raw),
        summary=df_to_records(summary),
        all_correct=bool(raw["correct"].all()),
        trials=trials,
    )


@app.post("/api/frequency")
def api_frequency():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify(error="Choose a file first."), 400
    data = upload.read()
    freq = bit_frequency(data)
    table = byte_frequency(data)
    top = table.sort_values("count", ascending=False).head(16)
    return jsonify(
        bytes=len(data),
        ones_fraction=freq["ones_fraction"],
        zeros_fraction=freq["zeros_fraction"],
        top_bytes=df_to_records(top),
        all_bytes=df_to_records(table),
    )


@app.post("/api/avalanche")
def api_avalanche():
    body = request.get_json(silent=True) or {}
    algorithm = body.get("algorithm", "")
    message = body.get("message", "")
    if algorithm not in ALGORITHMS:
        return jsonify(error="Unsupported algorithm."), 400
    if not message:
        return jsonify(error="Type a short message first."), 400
    return jsonify(avalanche_demo(algorithm, message.encode("utf-8")))


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is larger than 4 MB. Vercel limits request size; use a smaller file."), 413


@app.get("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cryptographic Algorithm Comparison Lab</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --paper:#f2f5f6; --panel:#ffffff; --ink:#14232b; --muted:#566a74; --line:#cfdadf;
  --accent:#1f4e79; --des:#b5483a; --aes:#1f6f8b; --chacha:#5b7f3a; --warn-bg:#fbeae6; --ok-bg:#e6f2e9;
}
@media (prefers-color-scheme: dark){
  :root{ --paper:#0f1a20; --panel:#16252d; --ink:#e6eef1; --muted:#9db0b9; --line:#2a3d47;
         --accent:#6fb0e6; --warn-bg:#3a1f1a; --ok-bg:#1b3324; --des:#e0786a; --aes:#5bb5d1; --chacha:#98c472; }
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 "IBM Plex Sans",system-ui,sans-serif}
header{padding:40px 24px 24px;max-width:1080px;margin:0 auto}
h1{font:600 clamp(28px,4.5vw,44px)/1.1 "Newsreader",Georgia,serif;margin:0 0 8px;letter-spacing:-.01em}
h2{font:600 22px/1.2 "Newsreader",Georgia,serif;margin:0 0 12px}
header p{margin:0;color:var(--muted);max-width:62ch}
.notice{max-width:1032px;margin:0 auto 16px;padding:12px 16px;background:var(--warn-bg);border-left:4px solid var(--des);border-radius:4px}
main{max-width:1080px;margin:0 auto;padding:0 24px 64px}
nav{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:16px 0 24px;flex-wrap:wrap}
nav button{background:none;border:0;border-bottom:3px solid transparent;padding:10px 14px;font:500 15px "IBM Plex Sans",sans-serif;color:var(--muted);cursor:pointer}
nav button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent)}
nav button:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
section.tab{display:none}
section.tab.active{display:block}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:20px;margin-bottom:20px}
.row{display:flex;gap:24px;flex-wrap:wrap}
.row > div{flex:1 1 260px}
label.opt{display:flex;gap:8px;align-items:center;margin:6px 0}
input[type=number],select,textarea,input[type=file]{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:4px;background:var(--paper);color:var(--ink);font:inherit}
button.primary{background:var(--accent);color:#fff;border:0;border-radius:4px;padding:10px 18px;font:600 15px "IBM Plex Sans",sans-serif;cursor:pointer}
@media (prefers-color-scheme: dark){ button.primary{color:#0f1a20} }
button.primary:disabled{opacity:.5;cursor:wait}
button.secondary{background:transparent;color:var(--accent);border:1px solid var(--accent);border-radius:4px;padding:8px 14px;font:500 14px "IBM Plex Sans",sans-serif;cursor:pointer;margin-right:8px}
.status{margin:12px 0;min-height:1.5em;color:var(--muted)}
.status.error{color:var(--des);font-weight:500}
.banner{padding:10px 14px;border-radius:4px;margin:12px 0}
.banner.ok{background:var(--ok-bg)} .banner.bad{background:var(--warn-bg)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}
th{font-weight:600;background:var(--paper)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.chartbox{position:relative;height:320px;margin:12px 0 24px}
.small{color:var(--muted);font-size:14px}
ol li{margin:6px 0}
.metrics{display:flex;gap:24px;flex-wrap:wrap;margin:12px 0}
.metrics div{min-width:120px}.metrics b{display:block;font-size:22px}
@media (prefers-reduced-motion: no-preference){ button.primary{transition:opacity .15s} }
</style>
</head>
<body>
<header>
  <h1>Cryptographic Algorithm Comparison Lab</h1>
  <p>Compare DES-CBC, AES-256-GCM and ChaCha20-Poly1305 on the same input: speed, package size, correctness and a one-bit avalanche check.</p>
</header>
<div class="notice">DES is obsolete and is included only for classroom comparison. Never use it to protect real data. This is not a production security product.</div>
<main>
<nav role="tablist">
  <button role="tab" aria-selected="true" data-tab="bench">Benchmark</button>
  <button role="tab" aria-selected="false" data-tab="stats">Statistical observations</button>
  <button role="tab" aria-selected="false" data-tab="params">Parameters and environment</button>
  <button role="tab" aria-selected="false" data-tab="help">How to use</button>
</nav>

<section class="tab active" id="tab-bench">
  <div class="panel">
    <div class="row">
      <div>
        <h2>Algorithms</h2>
        <div id="algList"></div>
        <h2 style="margin-top:20px">Trials</h2>
        <input type="number" id="trials" value="10" min="3" max="30">
        <p class="small">3 to 30 trials per file and algorithm. Use 10 or more for the course experiment.</p>
      </div>
      <div>
        <h2>Input</h2>
        <label class="opt"><input type="radio" name="src" value="sample" checked> Built-in reproducible samples</label>
        <label class="opt"><input type="radio" name="src" value="upload"> Upload one file (up to 4 MB)</label>
        <div id="sampleBox"></div>
        <div id="uploadBox" style="display:none"><input type="file" id="benchFile"></div>
      </div>
    </div>
    <p class="small">Each selected input is tested unchanged against each selected algorithm. Setup time (key and nonce creation, cipher initialisation) is recorded separately from encryption and decryption time.</p>
    <button class="primary" id="runBtn">Run experiments</button>
    <div class="status" id="benchStatus" role="status"></div>
  </div>
  <div id="benchResults"></div>
</section>

<section class="tab" id="tab-stats">
  <div class="panel">
    <h2>Bit and byte frequency</h2>
    <p class="small">Descriptive observations only, not cryptanalysis or proof of security.</p>
    <input type="file" id="freqFile">
    <p><button class="primary" id="freqBtn">Analyse file</button></p>
    <div class="status" id="freqStatus" role="status"></div>
    <div id="freqResult"></div>
  </div>
  <div class="panel">
    <h2>One-bit-flip avalanche observation</h2>
    <label for="avAlg">Algorithm</label>
    <select id="avAlg"></select>
    <label for="avMsg" style="display:block;margin-top:12px">Short sample message</label>
    <textarea id="avMsg" rows="2">Cryptography lab example</textarea>
    <p><button class="primary" id="avBtn">Run avalanche observation</button></p>
    <div class="status" id="avStatus" role="status"></div>
    <div id="avResult"></div>
    <p class="small">One controlled observation with fixed lab-only parameters. It is not a security certificate.</p>
  </div>
</section>

<section class="tab" id="tab-params">
  <div class="panel">
    <h2>Documented comparison parameters</h2>
    <div class="scroll" id="paramTable"></div>
    <p class="small">DES uses a 64-bit key representation with 56 effective key bits. AES and ChaCha use 256-bit keys. Nonces, IVs and authentication tags add to the stored package size.</p>
  </div>
  <div class="panel">
    <h2>Current computer and library versions</h2>
    <div class="scroll" id="envTable"></div>
    <p class="small">This shows the Vercel server that runs the benchmark, not your own computer. Timings can vary between runs on shared servers.</p>
  </div>
</section>

<section class="tab" id="tab-help">
  <div class="panel">
    <h2>Reproducible workflow</h2>
    <ol>
      <li>Select the same samples and algorithms for every run.</li>
      <li>Use at least 10 trials (20 or more if practical).</li>
      <li>Confirm the correctness banner says every decryption recovered the original input.</li>
      <li>Download the raw and summary CSV files and keep them with your report.</li>
      <li>Compare median values and ranges, and explain the machine and software differences.</li>
      <li>Do not claim that timing, frequency or avalanche observations prove security.</li>
    </ol>
    <p><b>Fairness limitation.</b> DES-CBC is unauthenticated and uses padding. AES-GCM and ChaCha20-Poly1305 are authenticated encryption. Their security properties differ, so speed results are implementation observations and not a universal ranking.</p>
    <p><b>Nonce rule.</b> Never reuse a nonce with the same key in AES-GCM or ChaCha20-Poly1305. This benchmark creates a fresh random key and nonce for every trial.</p>
  </div>
</section>
</main>

<script>
const $ = id => document.getElementById(id);
const COLORS = {"DES-CBC (educational)":"#b5483a","AES-256-GCM":"#1f6f8b","ChaCha20-Poly1305":"#5b7f3a"};
let charts = [], lastRaw = [], lastSummary = [];

function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function fmt(v){ return typeof v === "number" && !Number.isInteger(v) ? v.toFixed(4) : v; }
function tableHTML(rows, cols){
  if(!rows.length) return "<p class='small'>No data.</p>";
  cols = cols || Object.keys(rows[0]);
  return "<table><thead><tr>" + cols.map(c=>"<th>"+esc(c)+"</th>").join("") + "</tr></thead><tbody>" +
    rows.map(r=>"<tr>"+cols.map(c=>"<td class='"+(typeof r[c]==="number"?"num":"")+"'>"+esc(fmt(r[c]))+"</td>").join("")+"</tr>").join("") +
    "</tbody></table>";
}
function toCSV(rows){
  if(!rows.length) return "";
  const cols = Object.keys(rows[0]);
  const q = v => '"' + String(v).replace(/"/g,'""') + '"';
  return [cols.join(",")].concat(rows.map(r=>cols.map(c=>q(r[c])).join(","))).join("\n");
}
function download(name, rows){
  const url = URL.createObjectURL(new Blob([toCSV(rows)], {type:"text/csv"}));
  const a = document.createElement("a"); a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}
function setStatus(el, msg, isError){ el.textContent = msg; el.className = "status" + (isError ? " error" : ""); }

// tabs
document.querySelectorAll("nav button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll("nav button").forEach(x => x.setAttribute("aria-selected", x === b));
  document.querySelectorAll("section.tab").forEach(s => s.classList.remove("active"));
  $("tab-" + b.dataset.tab).classList.add("active");
}));
document.querySelectorAll("input[name=src]").forEach(r => r.addEventListener("change", () => {
  const up = document.querySelector("input[name=src]:checked").value === "upload";
  $("uploadBox").style.display = up ? "block" : "none";
  $("sampleBox").style.display = up ? "none" : "block";
}));

async function init(){
  try {
    const info = await (await fetch("/api/info")).json();
    $("trials").max = info.max_trials;
    $("algList").innerHTML = info.algorithms.map(a =>
      `<label class="opt"><input type="checkbox" name="alg" value="${esc(a)}" checked> ${esc(a)}</label>`).join("");
    $("sampleBox").innerHTML = info.samples.map(s =>
      `<label class="opt"><input type="checkbox" name="sample" value="${esc(s)}" ${info.default_samples.includes(s) ? "checked" : ""}> ${esc(s)}</label>`).join("");
    $("avAlg").innerHTML = info.algorithms.map(a => `<option>${esc(a)}</option>`).join("");
    $("paramTable").innerHTML = tableHTML(info.params);
    $("envTable").innerHTML = tableHTML(Object.entries(info.environment).map(([k,v]) => ({Item:k, Value:v})));
  } catch(e) {
    setStatus($("benchStatus"), "Could not load lab settings. Refresh the page.", true);
  }
}

function drawChart(canvasId, summary, metric, title){
  const datasets = [...new Set(summary.map(r => r.dataset))];
  const algs = [...new Set(summary.map(r => r.algorithm))];
  const ch = new Chart($(canvasId), {
    type: "bar",
    data: { labels: datasets, datasets: algs.map(a => ({
      label: a, backgroundColor: COLORS[a] || "#1f4e79",
      data: datasets.map(d => { const r = summary.find(x => x.dataset === d && x.algorithm === a); return r ? r[metric] : 0; })
    }))},
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { title: { display: true, text: title } },
      scales: { y: { title: { display: true, text: "Median time (ms)" }, beginAtZero: true } } }
  });
  charts.push(ch);
}

$("runBtn").addEventListener("click", async () => {
  const fd = new FormData();
  document.querySelectorAll("input[name=alg]:checked").forEach(c => fd.append("algorithms", c.value));
  fd.append("trials", $("trials").value);
  const upload = document.querySelector("input[name=src]:checked").value === "upload";
  if (upload) { const f = $("benchFile").files[0]; if (f) fd.append("file", f); }
  else document.querySelectorAll("input[name=sample]:checked").forEach(c => fd.append("samples", c.value));

  $("runBtn").disabled = true;
  setStatus($("benchStatus"), "Running experiments. This can take several seconds...");
  try {
    const res = await fetch("/api/benchmark", {method:"POST", body: fd});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Benchmark failed.");
    lastRaw = data.raw; lastSummary = data.summary;
    charts.forEach(c => c.destroy()); charts = [];
    const cols = ["dataset","algorithm","input_bytes","package_bytes_median","encryption_median_ms","encryption_range_ms","decryption_median_ms","decryption_range_ms","encryption_setup_median_ms","all_correct"];
    $("benchResults").innerHTML = `
      <div class="panel">
        <h2>Summary (median and range)</h2>
        <div class="banner ${data.all_correct ? "ok" : "bad"}">${data.all_correct
          ? "All tested decryptions recovered the exact original input."
          : "At least one decryption correctness check failed. Do not use these results."}</div>
        <div class="scroll">${tableHTML(data.summary, cols)}</div>
        <p style="margin-top:16px"><button class="secondary" id="dlSummary">Download summary_results.csv</button>
        <button class="secondary" id="dlRaw">Download raw_results.csv</button></p>
      </div>
      <div class="panel">
        <h2>Median operation times</h2>
        <div class="chartbox"><canvas id="chEnc"></canvas></div>
        <div class="chartbox"><canvas id="chDec"></canvas></div>
      </div>
      <div class="panel">
        <h2>Raw trial records (first 50 of ${data.raw.length})</h2>
        <div class="scroll">${tableHTML(data.raw.slice(0, 50))}</div>
      </div>`;
    drawChart("chEnc", data.summary, "encryption_median_ms", "Median encryption time");
    drawChart("chDec", data.summary, "decryption_median_ms", "Median decryption time");
    $("dlSummary").onclick = () => download("summary_results.csv", lastSummary);
    $("dlRaw").onclick = () => download("raw_results.csv", lastRaw);
    setStatus($("benchStatus"), "Experiment finished. Check correctness before interpreting timing.");
  } catch (e) {
    setStatus($("benchStatus"), e.message, true);
  } finally {
    $("runBtn").disabled = false;
  }
});

$("freqBtn").addEventListener("click", async () => {
  const f = $("freqFile").files[0];
  if (!f) { setStatus($("freqStatus"), "Choose a file first.", true); return; }
  const fd = new FormData(); fd.append("file", f);
  setStatus($("freqStatus"), "Analysing...");
  try {
    const res = await fetch("/api/frequency", {method:"POST", body: fd});
    const d = await res.json();
    if (!res.ok) throw new Error(d.error || "Analysis failed.");
    $("freqResult").innerHTML = `<div class="metrics">
      <div><b>${d.bytes.toLocaleString()}</b>Bytes</div>
      <div><b>${d.ones_fraction.toFixed(4)}</b>Bit ones</div>
      <div><b>${d.zeros_fraction.toFixed(4)}</b>Bit zeros</div></div>
      <h2 style="font-size:18px">16 most frequent byte values</h2>
      <div class="scroll">${tableHTML(d.top_bytes)}</div>
      <p style="margin-top:12px"><button class="secondary" id="dlFreq">Download byte_frequency.csv</button></p>`;
    $("dlFreq").onclick = () => download("byte_frequency.csv", d.all_bytes);
    setStatus($("freqStatus"), "");
  } catch (e) { setStatus($("freqStatus"), e.message, true); }
});

$("avBtn").addEventListener("click", async () => {
  setStatus($("avStatus"), "Running...");
  try {
    const res = await fetch("/api/avalanche", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({algorithm: $("avAlg").value, message: $("avMsg").value})});
    const d = await res.json();
    if (!res.ok) throw new Error(d.error || "Avalanche run failed.");
    $("avResult").innerHTML = `<div class="metrics">
      <div><b>${d.different_bits}</b>Different bits</div>
      <div><b>${d.compared_bits}</b>Compared bits</div>
      <div><b>${d.difference_fraction.toFixed(4)}</b>Difference fraction</div></div>`;
    setStatus($("avStatus"), "");
  } catch (e) { setStatus($("avStatus"), e.message, true); }
});

init();
</script>
</body>
</html>
"""
