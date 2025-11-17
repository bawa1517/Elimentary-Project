# ECL Dashboard (Streamlit)

Minimal, production-ready Streamlit application for Expected Credit Loss (ECL) analysis with auditability and governance.

## Overview
- Loads `loan_data.csv`, cleans and encodes features.
- Trains a simple Probability of Default (PD) model using Logistic Regression.
- Computes ECL as `PD × LGD × EAD`.
- Aggregates by `loan_intent` and `person_gender`, applying action rules.
- Provides AI Insights via Gemini to summarize risk and recommendations.
- Saves ECL reports and analyst insights for CRO review and audit.

## Data & Preprocessing
- Numeric columns are coerced to numeric and imputed with median.
- Categorical columns are imputed with mode.
- Target `loan_status` is converted to 0/1 default flag.

## Modeling (PD)
- `OneHotEncoder(handle_unknown="ignore")` for categorical features.
- `LogisticRegression(class_weight="balanced", max_iter=500)` for PD.

## ECL Computation
- LGD by `loan_intent`:
  - `education=0.3`, `business=0.5`, `medical=0.4`, `venture=0.6`, others `0.45`.
- EAD = `loan_amnt`.
- ECL = `pd × lgd × ead`.

## Action Rules
- `ECL > 1.5 × median` → Reduce disbursement
- `ECL > 1.1 × median` → Increase interest rate
- Else → Monitor

## App Features
- Sidebar filters for `loan_intent` and `person_gender`.
- Summary table with `pd_mean`, `lgd`, `ecl`, `action`.
- Bar chart of ECL by gender.
- AI Insight (Gemini): concise risk guidance for selected segments.
- Save ECL reports (`reports/report_*.csv`).
- Save analyst insights (`insights.csv`) and CRO decisions.

## Files
- `app.py` — Streamlit UI
- `data.py` — load & clean
- `pd_model.py` — PD modeling
- `ecl.py` — ECL, aggregation, rules
- `ai.py` — Gemini integration
- `storage.py` — reports & insights storage
- `loan_data.csv` — dataset
- `requirements.txt` — dependencies

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment (Render)
- Create a new Web Service from your GitHub repo.
- Build: `pip install -r requirements.txt`
- Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Optional env var: `GEMINI_API_KEY` (update `ai.py` to read from env for production).

## Security & Governance
- No PII stored; only aggregated segments and audit notes.
- Persisted artifacts in CSV for auditability and portability.

## Methodology & Design
- Simple, explainable PD model.
- Deterministic LGD mapping per business rules.
- Action rules driven by median thresholds.
- Modular design to keep code minimal and testable.

## License
Internal/educational use. Adapt as needed for production.

