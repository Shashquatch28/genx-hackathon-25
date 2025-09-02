from typing import Dict, List, Optional
from app.services.genai_client import generate_content
from app.services.contextualizer.templates import UserContext, build_prompt

# Simple type-specific hints (swap for RAG later)
_RAG_HINTS: Dict[str, List[str]] = {
    "lease": [
        "California AB 12: For most rentals, security deposits for agreements on/after July 1, 2024 are capped at one month’s rent; small-landlord exceptions exist.",  # refs AB 12
        "AB 1482: Many CA units have rent increases capped at 5% + CPI, up to 10%, depending on timing and CPI; check local ordinances and applicability.",
        "Clarify ‘fees’ vs ‘deposits’: non-refundable fees should map to a specific service; deposits are generally refundable less lawful deductions."
    ],
    "employment": [
        "Non-compete clauses may be unenforceable in some jurisdictions (e.g., CA); verify current rules.",
        "Confidentiality obligations can survive termination; clarify scope and duration."
    ],
}


def get_rag_hints(contract_type: Optional[str], clause_text: str) -> List[str]:
    if not contract_type:
        return []
    return _RAG_HINTS.get(contract_type.lower(), [])[:3]

def generate_contextualized_explanation(
    clause_text: str,
    ctx_dict: Dict
) -> Dict:
    ctx = UserContext(
        role=ctx_dict.get("role", "reader"),
        location=ctx_dict.get("location"),
        contract_type=ctx_dict.get("contract_type"),
        interests=ctx_dict.get("interests"),
        tone=ctx_dict.get("tone", "plain"),
    )
    hints = get_rag_hints(ctx.contract_type, clause_text)
    prompt = build_prompt(clause_text, ctx, hints=hints)
    text = generate_content(prompt)
    return {
        "clause": clause_text,
        "context": ctx_dict,
        "explanation": text or "For you, this means… (no response)",
        "used_hints": hints,
    }
