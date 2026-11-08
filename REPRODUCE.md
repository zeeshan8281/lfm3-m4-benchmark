# Reproduction

Use Apple Silicon with enough free disk and memory. The measured installation used Python3.12.13, mlx-vlm0.7.12 and MLX0.32.4. Full dependency pins are in evidence/requirements-freeze.txt.

Create an isolated runtime/venv, install those pins, and fetch the 13 files listed in evidence/download-manifest.json from LiquidAI/LFM3-1.7B-MLX-4bit revision91f34088d6946482cbcae11b85d4657093618c34 into model/. Validate lengths and the recorded hashes before execution. Model files are intentionally not redistributed with this report. Respect the linked model license.

Run from this folder:

```bash
runtime/venv/bin/python harness.py --mode selfcheck
runtime/venv/bin/python harness.py --mode smoke --output runs/new-smoke.jsonl
```

The campaign runner uses fixed output names and refuses to overwrite existing JSONL. Preserve the supplied evidence and use a fresh reproduction directory for a new campaign:

```bash
python3 run_campaign.py
python3 summarize.py
python3 audit_results.py
uv run --with matplotlib python plot_results.py
```

Run one inference job at a time. The runner forces offline Hugging Face access after the pinned files are installed. No automatic remote fallback is used. Refer to protocol.md and REPORT.md for timing exclusions, process-cold limitations, functional scoring and synchronous-engine scope.
