import json
from vertex_ai import generate_content
from risk_keywords import RISKY_TERMS, find_keyword_flags

def call_gemini_for_risk(clause_text: str) -> list:
    prompt_text = (
        f'Highlight potential high-risk terms in this clause: '
        f'"{{clause_text}}". Return STRICTLY a valid JSON object with this format:'
        f'{{"flags": [{{"term": "...", "explanation": "..."}}]}}'
    )
    try:
        # Call new generative model interface
        output_text = generate_content(prompt_text)

        #Debug Gemini output
        print("Raw Gemini output:", repr(output_text))

        # Parse JSON output text
        try:
            contextual_flags = json.loads(output_text).get("flags", [])
        except Exception:
            contextual_flags = []
        return contextual_flags
    except Exception as e:
        print(f"[RiskRadar] Error parsing Gemini response: {e}")
        return []

def generate_risk_radar_response(clause_text: str) -> dict:
    keyword_flags = find_keyword_flags(clause_text, RISKY_TERMS)
    contextual_flags = call_gemini_for_risk(clause_text)
    risk_count = len(keyword_flags) + len(contextual_flags)
    return {
        "flagged_clauses": [
            {
                "clause": clause_text,
                "keyword_flags": keyword_flags,
                "contextual_flags": contextual_flags,
            }
        ],
        "risk_summary": f"{risk_count} high-risk terms detected: "
                        f"{len(keyword_flags)} keyword-based, "
                        f"{len(contextual_flags)} contextual.",
    }
