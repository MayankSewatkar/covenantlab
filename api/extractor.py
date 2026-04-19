import json
import os
import anthropic
from typing import Dict, List

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

EXTRACTION_SYSTEM = """You are a financial covenant analyst with deep expertise in leveraged finance
and credit agreement documentation. Extract structured data precisely.
Return ONLY valid JSON. No commentary, no markdown, no code fences."""

CLAUSE_PROMPT = """Analyze this {clause_type} covenant clause from a credit agreement and extract:

1. threshold: numeric limit (value, unit: USD/x_EBITDA/percent/ratio, description)
2. basket_size: fixed_amount (number), grower_component (string if any), description
3. conditions: list of {{metric, operator (>=/<=/>/</=), value, description}}
4. restrictions: list of specific prohibited or limited actions (strings)
5. exceptions: list of carve-outs or permitted exceptions (strings)
6. risk_flags: list of {{flag, severity (low/medium/high), rationale}}
   Flag HIGH for: unlimited baskets, cov-lite features, EBITDA add-backs beyond 12 months,
   portability provisions, snooze/extend, missing maintenance tests.
   Flag MEDIUM for: large fixed baskets >$200M, grower baskets, simple majority amendments.
7. confidence: float 0.0-1.0

Clause text:
\"\"\"{clause_text}\"\"\"

Return JSON exactly:
{{
  "threshold": {{}},
  "basket_size": {{}},
  "conditions": [],
  "restrictions": [],
  "exceptions": [],
  "risk_flags": [],
  "confidence": 0.85
}}"""

def extract_clause(clause: Dict) -> Dict:
    prompt = CLAUSE_PROMPT.format(
        clause_type=clause["clause_type"].replace("_", " ").title(),
        clause_text=clause["raw_text"][:3000]
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=EXTRACTION_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    raw_json = response.content[0].text.strip()
    try:
        extracted = json.loads(raw_json)
    except json.JSONDecodeError:
        extracted = {
            "threshold": {}, "basket_size": {}, "conditions": [],
            "restrictions": [], "exceptions": [], "risk_flags": [], "confidence": 0.0
        }
    return {**clause, **extracted}

def extract_all_clauses(clauses: List[Dict]) -> List[Dict]:
    return [extract_clause(c) for c in clauses]
