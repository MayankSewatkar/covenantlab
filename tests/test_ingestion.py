import sys
sys.path.insert(0, "../api")

from ingestion import clean_text, segment_clauses

SAMPLE_TEXT = """
Section 6.01. Incurrence of Indebtedness. The Borrower shall not incur any
Indebtedness unless the Total Leverage Ratio would not exceed 4.50 to 1.00.

Section 6.04. Restricted Payments. The Borrower shall not declare any Restricted
Payment unless no Default exists and Total Leverage Ratio is below 3.50x.

Section 9.02. Amendments and Waivers. No amendment shall be effective without
consent of Required Lenders holding more than 50% of Commitments.
"""

def test_clean_text_removes_extra_whitespace():
    raw = "hello    world\n\n\n\nfoo"
    cleaned = clean_text(raw)
    assert "    " not in cleaned
    assert "\n\n\n" not in cleaned

def test_segment_detects_debt_incurrence():
    clauses = segment_clauses(SAMPLE_TEXT)
    types = [c["clause_type"] for c in clauses]
    assert "debt_incurrence" in types

def test_segment_detects_restricted_payments():
    clauses = segment_clauses(SAMPLE_TEXT)
    types = [c["clause_type"] for c in clauses]
    assert "restricted_payments" in types

def test_segment_detects_amendment():
    clauses = segment_clauses(SAMPLE_TEXT)
    types = [c["clause_type"] for c in clauses]
    assert "amendment_voting" in types

def test_clause_text_nonempty():
    clauses = segment_clauses(SAMPLE_TEXT)
    for c in clauses:
        assert len(c["raw_text"]) > 10

if __name__ == "__main__":
    test_clean_text_removes_extra_whitespace()
    test_segment_detects_debt_incurrence()
    test_segment_detects_restricted_payments()
    test_segment_detects_amendment()
    test_clause_text_nonempty()
    print("All ingestion tests passed.")
