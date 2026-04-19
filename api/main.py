import os
import tempfile
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ingestion import ingest_document
from extractor import extract_all_clauses
from scorer import compute_overall_score
from backtest import run_backtest

app = FastAPI(title="CovenantLab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.post("/analyze")
async def analyze_agreement(file: UploadFile = File(...)):
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files supported.")

    suffix = ".pdf" if file.filename.endswith(".pdf") else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        clauses = ingest_document(tmp_path)
        if not clauses:
            raise HTTPException(status_code=422, detail="No covenant clauses detected in document.")

        extracted = extract_all_clauses(clauses)
        scoring = compute_overall_score(extracted)

        return JSONResponse({
            "status": "success",
            "filename": file.filename,
            "extracted_at": datetime.utcnow().isoformat(),
            "clause_count": len(extracted),
            "covenants": extracted,
            "scoring": scoring,
        })
    finally:
        os.unlink(tmp_path)

@app.get("/backtest")
def backtest():
    results = run_backtest("../data/synthetic_deals.csv")
    return JSONResponse(results)

@app.post("/score-text")
async def score_raw_text(payload: dict):
    """Accept raw clause text for quick scoring without file upload."""
    clauses = payload.get("clauses", [])
    if not clauses:
        raise HTTPException(status_code=400, detail="Provide a list of {clause_type, raw_text}.")
    extracted = extract_all_clauses(clauses)
    scoring = compute_overall_score(extracted)
    return JSONResponse({"covenants": extracted, "scoring": scoring})
