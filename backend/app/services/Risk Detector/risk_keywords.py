import re

RISKY_TERMS = {
    "indemnify": "Potential liability concern",
    "penalty": "May indicate financial risk",
    "late fee": "Additional charges if payment is delayed",
    "breach": "Violation of contract terms",
    "terminate": "Contract termination risk",
    "liability": "Potential responsibility for loss or damage",
    "damages": "Risk of financial penalty",
    "dispute resolution": "May require arbitration or litigation",
    "arbitration": "Binding dispute resolution mechanism",
    "waiver": "Possible loss of rights",
    "default": "Failure to fulfill obligations",
    "deposit forfeiture": "Loss of security deposit",
    "cancellation": "Termination rights and penalties",
    "force majeure": "Excused non-performance due to extraordinary events",
    "confidentiality breach": "Risk of exposing sensitive information",
    "extension denial": "No right to extend contract",
    "renewal obligation": "Mandatory contract renewal terms",
    "limitation of liability": "Caps on damages recoverable",
    "damages cap": "Limit on financial liability",
    "governing law": "Jurisdiction controlling contract interpretation",
    "jurisdiction": "Legal authority over disputes",
    "subrogation": "Rights to claim from third parties",
    "hold harmless": "Agreement to assume liability",
    "insurance requirements": "Required insurance coverage to mitigate risk",
    "non-compete": "Restricts certain business activities",
    "exclusivity": "Limits parties to a single agreement or supplier",
    "termination for convenience": "Allows termination without cause",
    "assignment restriction": "Limits transfer of contractual rights",
    "security deposit": "Funds held to secure obligations",
    "rent escalation": "Terms for increasing rent",
    "renewal period": "Length and conditions of contract renewal",
    "notice requirements": "Formal communication obligations",
}

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower())

def find_keyword_flags(clause_text: str, risky_terms: dict) -> list:
    normalized = normalize_text(clause_text)
    flags = []
    for term, explanation in risky_terms.items():
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, normalized):
            flags.append({"term": term, "predefined_explanation": explanation})
    return flags
