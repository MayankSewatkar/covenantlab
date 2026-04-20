from typing import List, Dict

CLAUSE_WEIGHTS = {
    "debt_incurrence":       0.30,
    "restricted_payments":   0.20,
    "asset_sales":           0.20,
    "collateral_guarantees": 0.15,
    "amendment_voting":      0.15,
}

RISK_FLAG_PENALTIES = {"high": 25, "medium": 12, "low": 5}

def score_clause(clause: Dict) -> float:
    score = 100.0
    ctype = clause.get("clause_type")

    threshold = clause.get("threshold") or {}
    unit = threshold.get("unit", "")
    val = threshold.get("value")
    if unit in ("x_EBITDA", "ratio") and val is not None:
        if val > 6.0:   score -= 30
        elif val > 5.0: score -= 20
        elif val > 4.0: score -= 10
    if not val and ctype not in ("amendment_voting", "collateral_guarantees"):
        score -= 15

    basket = clause.get("basket_size") or {}
    if basket.get("grower_component"):
        score -= 15
    fixed = basket.get("fixed_amount") or 0
    if fixed > 500_000_000:
        score -= 15
    elif fixed > 200_000_000:
        score -= 8

    conditions = clause.get("conditions") or []
    if not conditions and ctype == "debt_incurrence":
        score -= 20

    exceptions = clause.get("exceptions") or []
    if len(exceptions) > 10:
        score -= 20
    elif len(exceptions) > 5:
        score -= 10

    flag_penalty = sum(
        RISK_FLAG_PENALTIES.get(f.get("severity", "low"), 0)
        for f in (clause.get("risk_flags") or [])
    )
    score -= min(flag_penalty, 50)

    confidence = clause.get("confidence") or 1.0
    if confidence < 0.5:
        score -= 10

    return round(max(0.0, min(100.0, score)), 2)

def score_to_grade(score: float) -> str:
    if score >= 80: return "A — Strong Creditor Protection"
    if score >= 65: return "B — Moderate Protection"
    if score >= 50: return "C — Weak / Cov-Lite"
    return "D — Minimal Protection"

def compute_overall_score(clauses: List[Dict]) -> Dict:
    scored = {}
    for clause in clauses:
        ctype = clause["clause_type"]
        clause["risk_score"] = score_clause(clause)
        # Keep highest score if duplicate clause types
        if ctype not in scored or clause["risk_score"] > scored[ctype]:
            scored[ctype] = clause["risk_score"]

    total = sum(scored.get(ctype, 0.0) * w for ctype, w in CLAUSE_WEIGHTS.items())

    return {
        "clause_scores": scored,
        "overall_score": round(total, 2),
        "grade": score_to_grade(total),
        "missing_clauses": [c for c in CLAUSE_WEIGHTS if c not in scored],
    }
