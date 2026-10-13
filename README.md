# Free Water Deficit — Adult Hypernatremia

A local-first calculator for **adult hypernatremia**. The browser app uses JavaScript and the Python CLI/API provide the same estimates; no server, account, or API key is needed to use the web calculator.

## Functions

- Estimate total body water (TBW, L) from body weight and a selected TBW fraction.
- Estimate free-water deficit (L) to a chosen sodium target.
- Estimate the **change in serum sodium per litre of infusate** with the Adrogué–Madias equation (not an infusion prescription).
- Export a single calculation as JSON, or process a local CSV in Python.

## Equations

```text
TBW (L) = weight (kg) × TBW fraction
Deficit (L) = TBW × (measured Na / target Na − 1)
Estimated ΔNa after 1 L = (infusate Na + infusate K − measured Na) / (TBW + 1)
```

Na and K are in mmol/L; concentrations and correction estimates are approximate. Suggested adult TBW fractions in the UI: adult male 0.60, adult female or older male 0.50, older female 0.45; a custom fraction is also supported.

## Use

The browser app is in [`web/index.html`](web/index.html). Serve it locally with `python -m http.server 8000 --directory web` and open `http://localhost:8000/`; JavaScript modules may not load over `file://`. No build is required. All inputs are processed **in the browser**; there are no third-party scripts, cookies, or data transmissions. JSON exports are generated locally. Avoid entering identifiable patient information.

```bash
python water_deficit.py single --weight-kg 60 --serum-sodium 166 --tbw-fraction 0.5
python water_deficit.py batch --input sample.csv --output results.csv
```

Batch CSV requires `weight_kg`, `serum_sodium`, and `tbw_fraction`; optional columns are `target_sodium`, `fluid_sodium`, and `fluid_potassium`. The entire file is validated before output is written. CSV data are processed locally.

An optional FastAPI server exposes `POST /api/water-deficit`:

```bash
python -m pip install -r requirements.txt
python cli.py serve
```

Other pre-existing agent audit endpoints remain for compatibility; their generic thresholds, placeholder modules, and simulated chat responses are **not validated clinical decision support**. The server provides no authentication and is intended for local development only. The pattern-based identifier check is not a reliable PHI-removal or HIPAA compliance guarantee; the audit log is process-local, not persistent.

## Verification

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/test_web.mjs  # Node.js 22 or newer
```

Python 3.10–3.12; modern Chrome, Firefox, Safari or Edge for the browser application. No Pyodide is required because the in-browser implementation is JavaScript.

## Clinical limitations

The formula does not account for ongoing water/electrolyte losses, volume depletion, changing kidney function, sodium or glucose disorders, or the timing and safety of correction. In hypovolaemia, resuscitation may be necessary before replacing free water. **Never use these outputs to automatically select a fluid rate or treatment without clinical reassessment and serial serum sodium monitoring.** Not validated for paediatric care.

Reference: [Yun et al. Evaluation and management of hypernatremia in adults (Korean J Intern Med, 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10175862/).

## License

[MIT](LICENSE).
