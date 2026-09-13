# Reasoning Error Inspector

A local FastAPI application that generates fresh factual reasoning from your question and evidence, then scores each hop with your existing trained probe. No training occurs in the app.

## Start on Windows

Use Python 3.12. Open PowerShell in this folder and run:

```powershell
.\start.ps1
```

If PowerShell blocks scripts, run these commands instead:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The page shows model loading status. The first start downloads the matching public Qwen weights (about 1 GB); subsequent starts reuse the project-local `.model-cache` folder (or your `HF_HOME`). Keep the terminal open. Stop with Ctrl+C. Use one worker, without auto-reload, so the model is loaded once.

On Linux/macOS:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

CPU is supported, with slower inference and float32 instead of the training run's GPU float16. Allow several GB of available RAM. A CUDA-enabled PyTorch installation uses an available compatible GPU automatically.

## Use

1. Enter a new question and paste its reference evidence, or upload a UTF-8 `.txt` or text-based `.pdf`.
2. Wait for **Model ready**, then click **Analyze reasoning**.
3. Inspect generated hops, their **error scores**, the highest-scoring hop, and the first threshold crossing. No threshold crossing is a valid outcome.
4. Read the **separate evidence check**. The probe localizes; the evidence component proposes a discrepancy. It can return insufficient information.
5. Click the report download button to export the result as PDF.
6. Optionally enable **Controlled test error** before analyzing again. This edits one source-matching generated numeric claim. If no eligible claim exists, the app asks for suitable evidence instead of pretending an error was inserted. The displayed answer precedes the edit.

The base Qwen model can fail to produce valid JSON. The app retries once and reports failure; it never scores malformed reasoning or silently swaps models. Uploaded PDFs need selectable text; there is no OCR. Long documents use disclosed TF-IDF excerpts. You can inspect exactly which evidence was used. File limits: 10 MB, 150 PDF pages, 250,000 extracted characters.

Generation uses plain completion for the base checkpoint, a fictional formatting example, a JSON syntax prefix, and stopping at a complete object. The example is never included in the probe's input. The evidence checker recognizes verbatim claims and unambiguous single-number differences between otherwise identical assertions. Other claims use a separate Qwen assessment with reference-quote validation. No injection metadata or error score is used for evidence judgments.

## Your included artifact

`backend/models/hop_error_probe.joblib` is a copy of your supplied artifact:

| Setting | Saved value |
|---|---|
| Model | `Qwen/Qwen2.5-0.5B` |
| Revision | `060db6499f32faf8b98477b0a26969ef7d8b9987` |
| Hidden-state layer | 13 |
| Feature width | 896 |
| Error-score threshold | 0.27 |
| Pooling | Last input token |
| Probe context limit | 2,048 tokens |
| Transformers | 5.16.1 |
| scikit-learn | 1.6.1 |

`run_config.json` and `environment_versions.json` were reconstructed from metadata embedded in this Joblib, not supplied independently. The Joblib metadata is authoritative. Startup validates model identity, revision, tokenizer fingerprint, hidden width, architecture, layer, and prompt/pooling version. Do not substitute an instruction-tuned model or another model size without a corresponding evaluated probe.

The app reproduces the notebook's `build_prefix` template, includes only hops up to the current hop, and extracts `hidden_states[13][0, -1, :]` from the same frozen checkpoint used for generation. Only that vector enters the saved classifier; evidence judgments and injection metadata do not.

