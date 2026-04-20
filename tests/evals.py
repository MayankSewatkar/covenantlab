"""
CovenantLab Extraction & Scoring Evals
Tests the full pipeline against ground truth for 5 clause types.
Run: python3 evals.py
"""
import sys, json, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from extractor import extract_clause
from scorer import score_clause, compute_overall_score

# ── Ground truth test cases ────────────────────────────────────────────────
EVAL_CASES = [
    {
        "id": "debt_strong",
        "clause_type": "debt_incurrence",
        "raw_text": """
        Section 6.01. Incurrence of Indebtedness. The Borrower shall not incur any
        additional Indebtedness unless, after giving pro forma effect thereto, the
        Total Net Leverage Ratio would not exceed 3.00 to 1.00. No grower basket,
        EBITDA add-backs, or builder baskets are permitted. All financial calculations
        shall use LTM Consolidated EBITDA without adjustment.
        """,
        "expected": {
            "threshold_unit": "ratio",
            "threshold_value_range": (2.5, 3.5),
            "has_grower": False,
            "min_risk_flags": 0,
            "max_risk_flags": 2,
            "score_range": (60, 100),
            "must_not_flag": ["EBITDA add-back", "grower basket"],
        }
    },
    {
        "id": "debt_weak",
        "clause_type": "debt_incurrence",
        "raw_text": """
        Section 6.01. Incurrence of Indebtedness. The Borrower may incur additional
        Indebtedness if the Total Net Leverage Ratio does not exceed 6.50 to 1.00
        on a pro forma basis. Additionally, a general basket permits incurrence up to
        the greater of $300,000,000 and 35% of Consolidated EBITDA (which includes
        projected synergies and cost savings for a 24-month forward period regardless
        of realization). Run-rate adjustments may be agreed bilaterally with the
        Administrative Agent without lender consent.
        """,
        "expected": {
            "threshold_unit": "ratio",
            "threshold_value_range": (6.0, 7.0),
            "has_grower": True,
            "min_risk_flags": 2,
            "score_range": (0, 40),
            "must_flag_severity": {"high": 2},
        }
    },
    {
        "id": "restricted_payments_moderate",
        "clause_type": "restricted_payments",
        "raw_text": """
        Section 6.04. Restricted Payments. The Borrower shall not declare or make any
        Restricted Payment unless no Default exists and the Total Net Leverage Ratio
        on a pro forma basis shall not exceed 4.00 to 1.00. A fixed basket of
        $75,000,000 per fiscal year is permitted without ratio compliance.
        Dividends to parent for tax distributions are permitted without limit.
        """,
        "expected": {
            "threshold_value_range": (3.5, 4.5),
            "min_risk_flags": 1,
            "score_range": (30, 70),
        }
    },
    {
        "id": "amendment_weak",
        "clause_type": "amendment_voting",
        "raw_text": """
        Section 9.02. Amendments. No amendment shall be effective without consent of
        Required Lenders holding more than 50% of outstanding Commitments. Any Lender
        may extend the maturity of its Loans without consent of other Lenders
        (Snooze/Extend). Voting rights may be transferred to affiliated funds without
        restriction or consent.
        """,
        "expected": {
            "min_risk_flags": 2,
            "score_range": (0, 55),
            "must_flag_keywords": ["snooze", "50%", "transfer"],
        }
    },
    {
        "id": "collateral_strong",
        "clause_type": "collateral_guarantees",
        "raw_text": """
        Section 6.09. Collateral. The Borrower shall grant a first priority perfected
        security interest in all assets to the Collateral Agent. A Collateral Coverage
        Ratio of not less than 1.75 to 1.00 shall be maintained quarterly. No
        Guarantor may be released without unanimous lender consent. After-acquired
        property must be pledged within 30 days.
        """,
        "expected": {
            "min_risk_flags": 0,
            "max_risk_flags": 4,
            "score_range": (65, 100),
        }
    },
]

# ── Eval runner ─────────────────────────────────────────────────────────────
def run_eval(case: dict) -> dict:
    result = extract_clause({
        "clause_type": case["clause_type"],
        "raw_text": case["raw_text"]
    })
    result["risk_score"] = score_clause(result)

    expected = case["expected"]
    failures = []
    passes = []

    # Check threshold unit
    if "threshold_unit" in expected:
        actual_unit = (result.get("threshold") or {}).get("unit", "")
        if actual_unit == expected["threshold_unit"]:
            passes.append(f"threshold_unit == {expected['threshold_unit']}")
        else:
            failures.append(f"threshold_unit: expected {expected['threshold_unit']}, got {actual_unit!r}")

    # Check threshold value range
    if "threshold_value_range" in expected:
        lo, hi = expected["threshold_value_range"]
        val = (result.get("threshold") or {}).get("value")
        if val is not None and lo <= val <= hi:
            passes.append(f"threshold_value {val} in [{lo}, {hi}]")
        else:
            failures.append(f"threshold_value: expected {lo}-{hi}, got {val}")

    # Check grower basket detection
    if "has_grower" in expected:
        actual_grower = bool((result.get("basket_size") or {}).get("grower_component"))
        if actual_grower == expected["has_grower"]:
            passes.append(f"has_grower == {expected['has_grower']}")
        else:
            failures.append(f"has_grower: expected {expected['has_grower']}, got {actual_grower}")

    # Check risk flag count
    flags = result.get("risk_flags") or []
    n_flags = len(flags)
    if "min_risk_flags" in expected and n_flags < expected["min_risk_flags"]:
        failures.append(f"risk_flags count: expected >= {expected['min_risk_flags']}, got {n_flags}")
    else:
        if "min_risk_flags" in expected:
            passes.append(f"risk_flag count {n_flags} >= {expected['min_risk_flags']}")
    if "max_risk_flags" in expected and n_flags > expected["max_risk_flags"]:
        failures.append(f"risk_flags count: expected <= {expected['max_risk_flags']}, got {n_flags}")

    # Check score range
    if "score_range" in expected:
        lo, hi = expected["score_range"]
        score = result["risk_score"]
        if lo <= score <= hi:
            passes.append(f"score {score:.1f} in [{lo}, {hi}]")
        else:
            failures.append(f"score: expected {lo}-{hi}, got {score:.1f}")

    # Check high-severity flag count
    if "must_flag_severity" in expected:
        for sev, min_count in expected["must_flag_severity"].items():
            actual = sum(1 for f in flags if f.get("severity") == sev)
            if actual >= min_count:
                passes.append(f"{sev} flags {actual} >= {min_count}")
            else:
                failures.append(f"{sev} flags: expected >= {min_count}, got {actual}")

    # Check for keywords in flag text (case-insensitive)
    if "must_flag_keywords" in expected:
        all_flag_text = " ".join(f.get("flag","") + f.get("rationale","") for f in flags).lower()
        for kw in expected["must_flag_keywords"]:
            if kw.lower() in all_flag_text:
                passes.append(f"keyword '{kw}' found in flags")
            else:
                failures.append(f"keyword '{kw}' NOT found in risk flags")

    # Check keywords that should NOT appear
    if "must_not_flag" in expected:
        all_flag_text = " ".join(f.get("flag","") + f.get("rationale","") for f in flags).lower()
        for kw in expected["must_not_flag"]:
            if kw.lower() not in all_flag_text:
                passes.append(f"correctly absent: '{kw}'")
            else:
                failures.append(f"false positive: '{kw}' flagged but should not be")

    return {
        "id": case["id"],
        "clause_type": case["clause_type"],
        "score": result["risk_score"],
        "confidence": result.get("confidence", 0),
        "n_flags": n_flags,
        "passes": passes,
        "failures": failures,
        "passed": len(failures) == 0,
    }

def main():
    print("=" * 60)
    print("CovenantLab Extraction & Scoring Evals")
    print("=" * 60)

    results = []
    for i, case in enumerate(EVAL_CASES):
        print(f"\n[{i+1}/{len(EVAL_CASES)}] Running: {case['id']} ({case['clause_type']})")
        r = run_eval(case)
        results.append(r)

        status = "PASS" if r["passed"] else "FAIL"
        print(f"  Status:     {status}")
        print(f"  Score:      {r['score']:.1f}  |  Confidence: {r['confidence']:.2f}  |  Flags: {r['n_flags']}")
        for p in r["passes"]:
            print(f"  ✓  {p}")
        for f in r["failures"]:
            print(f"  ✗  {f}")

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} passed ({100*passed//total}%)")
    print("=" * 60)

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results saved to eval_results.json")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
