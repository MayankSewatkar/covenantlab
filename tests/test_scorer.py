import sys
sys.path.insert(0, "../api")

from scorer import score_clause, compute_overall_score, score_to_grade

STRONG_CLAUSE = {
    "clause_type": "debt_incurrence",
    "threshold": {"value": 2.5, "unit": "x_EBITDA"},
    "basket_size": {"fixed_amount": 50_000_000, "grower_component": None},
    "conditions": [{"metric": "Total Leverage Ratio", "operator": "<=", "value": 2.5}],
    "restrictions": ["No additional debt above threshold"],
    "exceptions": ["Refinancing of existing debt"],
    "risk_flags": [],
    "confidence": 0.95,
}

WEAK_CLAUSE = {
    "clause_type": "debt_incurrence",
    "threshold": {"value": 7.0, "unit": "x_EBITDA"},
    "basket_size": {"fixed_amount": 600_000_000, "grower_component": "20% of EBITDA"},
    "conditions": [],
    "restrictions": [],
    "exceptions": ["Basket A", "Basket B", "Basket C", "Basket D", "Basket E", "Basket F"],
    "risk_flags": [
        {"flag": "EBITDA add-backs", "severity": "high", "rationale": "24-month synergies"},
        {"flag": "Grower basket", "severity": "medium", "rationale": "Expands with EBITDA"},
        {"flag": "Cov-lite", "severity": "high", "rationale": "No maintenance test"},
    ],
    "confidence": 0.88,
}

def test_strong_clause_scores_high():
    score = score_clause(STRONG_CLAUSE)
    assert score >= 70, f"Expected strong clause >= 70, got {score}"

def test_weak_clause_scores_low():
    score = score_clause(WEAK_CLAUSE)
    assert score <= 30, f"Expected weak clause <= 30, got {score}"

def test_overall_score_weights():
    clauses = [STRONG_CLAUSE.copy()]
    result = compute_overall_score(clauses)
    assert "overall_score" in result
    assert "grade" in result
    assert 0 <= result["overall_score"] <= 100

def test_grade_boundaries():
    assert "A" in score_to_grade(85)
    assert "B" in score_to_grade(70)
    assert "C" in score_to_grade(55)
    assert "D" in score_to_grade(30)

def test_missing_clauses_flagged():
    clauses = [STRONG_CLAUSE.copy()]
    result = compute_overall_score(clauses)
    assert "asset_sales" in result["missing_clauses"]

if __name__ == "__main__":
    test_strong_clause_scores_high()
    test_weak_clause_scores_low()
    test_overall_score_weights()
    test_grade_boundaries()
    test_missing_clauses_flagged()
    print("All tests passed.")
