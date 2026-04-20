# CovenantLab

**Credit Agreement Intelligence Platform** — upload a leveraged finance credit agreement, extract its covenant clauses with Claude AI, score creditor protections, and validate the scoring model against synthetic market outcome data.

---

## What It Does

CovenantLab ingests a credit agreement (PDF or TXT), locates the five legally significant covenant sections, sends each clause to Claude for structured extraction, and returns a numeric risk score with a letter grade. The interface has three tabs:

| Tab | Purpose |
|---|---|
| **Analyze Agreement** | Upload a document, extract covenants, view scores and risk flags |
| **Backtest Data** | Validate the scoring model against 200 synthetic historical deals |
| **Raw Scorer** | Paste a single clause and score it instantly, no file needed |

---

## Inputs

**Analyze Agreement** accepts:
- `.pdf` — full credit agreement (pdfplumber extracts the text)
- `.txt` — plain-text version of the agreement

The document must contain at least one of the five supported covenant section headers for extraction to succeed. Supported clause types and their regex-matched section titles:

| Clause Type | Matched Section Header |
|---|---|
| Debt Incurrence | "Incurrence of Indebtedness", "Debt Incurrence" |
| Restricted Payments | "Restricted Payments" |
| Asset Sales | "Asset Sales", "Asset Sale" |
| Collateral & Guarantees | "Collateral and Guarantees", "Collateral…Guarantee" |
| Amendment Voting | "Amendments and Waivers", "Waivers and Amendments" |

**Raw Scorer** accepts:
- A clause type selected from the dropdown
- Raw pasted text — any length, though the extractor uses the first 3,000 characters

---

## Extraction Pipeline

```
PDF/TXT upload
    │
    ▼
ingestion.py — pdfplumber text extraction → regex clause segmentation
    │
    ▼
extractor.py — Claude API (claude-sonnet-4-6, parallel threads)
    │           Structured JSON: threshold · basket_size · conditions
    │                            restrictions · exceptions · risk_flags · confidence
    ▼
scorer.py — deterministic rule-based scoring (0–100 per clause)
    │        weighted average → overall score → letter grade
    ▼
FastAPI /analyze → Streamlit frontend
```

### What Claude extracts per clause

| Field | Description |
|---|---|
| `threshold` | Numeric limit (value, unit: USD / x_EBITDA / ratio / percent, description) |
| `basket_size` | Fixed dollar amount, grower component (e.g. "greater of $X or Y% of EBITDA"), description |
| `conditions` | Metric-based tests required before the borrower can act (e.g. leverage ratio ≤ 4.0x) |
| `restrictions` | Specific prohibited or limited actions stated in the clause |
| `exceptions` | Carve-outs and permitted baskets (only what is explicitly stated) |
| `risk_flags` | Flagged provisions with severity (high / medium / low) and rationale |
| `confidence` | Model confidence 0.0–1.0 based on clause clarity |

---

## Scoring Model

Each clause receives a score from 0–100 using a deterministic ruleset in `scorer.py`. Higher = stronger creditor protection.

### Per-clause deductions

| Condition | Deduction |
|---|---|
| EBITDA ratio threshold > 6.0x | −30 |
| EBITDA ratio threshold 5.0–6.0x | −20 |
| EBITDA ratio threshold 4.0–5.0x | −10 |
| No numeric threshold (debt/payment/asset clauses) | −15 |
| Grower basket component present | −15 |
| Fixed basket > $500M | −15 |
| Fixed basket $200M–$500M | −8 |
| No financial conditions (debt incurrence only) | −20 |
| Exceptions list > 10 items | −20 |
| Exceptions list 6–10 items | −10 |
| HIGH severity risk flag | −25 (capped at −50 total) |
| MEDIUM severity risk flag | −12 |
| LOW severity risk flag | −5 |
| Extraction confidence < 0.5 | −10 |

### Weighted overall score

| Clause | Weight |
|---|---|
| Debt Incurrence | 30% |
| Restricted Payments | 20% |
| Asset Sales | 20% |
| Collateral & Guarantees | 15% |
| Amendment Voting | 15% |

### Letter grades

| Score | Grade |
|---|---|
| 80–100 | A — Strong Creditor Protection |
| 65–79 | B — Moderate Protection |
| 50–64 | C — Weak / Cov-Lite |
| 0–49 | D — Minimal Protection |

---

## Backtest Tab

The backtest validates that the scoring model is directionally predictive — i.e. that higher covenant scores correlate with better market outcomes.

### Dataset

A synthetic dataset of **200 deals** is generated via `api/backtest.py` using a seeded random model with the following structure:

| Column | Generation method |
|---|---|
| `covenant_score` | Uniform draw from 20–95 |
| `spread_at_issue` | 400 bps baseline + N(0, 80) noise |
| `spread_change` | −0.8 × score + N(0, 30) noise — encodes the hypothesis |
| `price_12m` | 95 + 0.05 × score + noise |
| `default_prob` | Logistic: 1 / (1 + e^(0.1 × (score − 50))) |
| `defaulted` | Binomial draw from `default_prob` |
| `recovery_rate` | Uniform 20–60% if defaulted, else NaN |

The −0.8 coefficient on spread change intentionally encodes a signal: deals with stronger covenants (higher scores) should show tighter spreads over time.

### Outputs

**Quartile summary** — deals split into four covenant score quartiles (Q1 Weakest → Q4 Strongest):
- Deal count, average score, average spread change, price at 12 months, default rate, average recovery rate

**Regression statistics** — OLS regression of covenant score → spread change:
- Pearson r, R², p-value, slope, intercept, sample size, significance flag

**Charts** — default rate by quartile (lower is better in Q4), average spread change by quartile (more negative = tightening = better)

---

## Raw Scorer Tab

Lets you score a single clause without uploading a full document. Useful for:
- Spot-checking a specific provision in isolation
- Comparing different versions of the same clause
- Testing the model on custom covenant language

**How it works:** the pasted text is sent directly to the `POST /score-text` endpoint, which skips ingestion and segmentation and calls the extractor and scorer directly.

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API framework | FastAPI 0.111+ |
| ASGI server | Uvicorn |
| AI extraction | Anthropic Claude (claude-sonnet-4-6) via `anthropic` Python SDK |
| PDF parsing | pdfplumber |
| Data processing | pandas, numpy |
| Statistics | scipy (Pearson r, OLS regression) |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` (parallel clause extraction) |
| Config | python-dotenv |

### Frontend
| Layer | Technology |
|---|---|
| UI framework | Streamlit 1.35+ |
| Charts | Plotly (go.Bar, dark theme) |
| HTTP client | requests |
| Styling | Custom CSS injected via `st.markdown(unsafe_allow_html=True)` |

### Language & Runtime
- Python 3.13
- Virtual environment: `.venv`

---

## Security

### API Key Handling
- The Anthropic API key is loaded exclusively from a `.env` file via `python-dotenv`
- `.env` is listed in `.gitignore` — it is never committed
- `.env.example` ships with a placeholder (`your_key_here`) to document the required variable without exposing credentials
- The key is never logged, returned in API responses, or surfaced in the frontend

### File Upload Safety
- Accepted MIME types are restricted to `.pdf` and `.txt` at both the FastAPI endpoint (`/analyze`) and the Streamlit file uploader
- Uploaded files are written to a `tempfile.NamedTemporaryFile` and deleted immediately after processing in a `finally` block — no persistent storage of uploaded documents
- File content is never echoed back to the client beyond the extracted structured data

### Document Privacy
- No uploaded document content is stored on disk beyond the duration of a single request
- Claude receives only the first 3,000 characters of each clause — the full document text is never forwarded to the API
- The backtest and raw scorer endpoints do not accept or process uploaded files

### Network
- CORS is currently set to `allow_origins=["*"]` — appropriate for local development; restrict to specific origins before deploying to production
- The API binds to `0.0.0.0` locally — restrict to `127.0.0.1` if the frontend and API run on the same host in production

### Prompt Injection
- Claude is given a strict system prompt instructing it to return only valid JSON with no commentary
- Extracted JSON is parsed with `json.loads`; any parse failure returns a safe zero-confidence fallback rather than propagating raw model output
- Clause text is inserted into the prompt as a quoted string, not as executable instructions

---

## Setup

```bash
git clone https://github.com/MayankSewatkar/covenantlab
cd covenantlab

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your Anthropic API key to .env

# Terminal 1 — API
cd api && uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && streamlit run app.py
```

Open `http://localhost:8501`.

---

## Project Structure

```
covenantlab/
├── api/
│   ├── main.py          # FastAPI app, route definitions
│   ├── ingestion.py     # PDF/TXT parsing, clause segmentation
│   ├── extractor.py     # Claude API calls, structured extraction
│   ├── scorer.py        # Deterministic scoring rules and grade bands
│   └── backtest.py      # Synthetic dataset generation and regression
├── frontend/
│   └── app.py           # Streamlit UI (three tabs)
├── data/
│   ├── synthetic_credit_agreement.txt   # Sample document for testing
│   └── synthetic_deals.csv              # Generated on first backtest run
├── tests/
│   ├── test_scorer.py
│   └── test_ingestion.py
├── .env.example
├── requirements.txt
└── README.md
```
