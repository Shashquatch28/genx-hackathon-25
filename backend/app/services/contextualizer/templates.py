from dataclasses import dataclass
from typing import Optional, List

@dataclass
class UserContext:
    role: str
    location: Optional[str] = None
    contract_type: Optional[str] = None
    interests: Optional[List[str]] = None
    tone: str = "plain"  # "plain" | "lawyer" | "exec"

def build_prompt(clause_text: str, ctx: UserContext, hints: Optional[List[str]] = None) -> str:
    tone_map = {
        "plain": "Explain in simple, plain English.",
        "lawyer": "Explain with legal detail and references where appropriate.",
        "exec": "Explain concisely for a time-pressed decision maker.",
    }
    tone_line = tone_map.get(ctx.tone, tone_map["plain"])

    interests_line = ""
    if ctx.interests:
        interests_line = "Emphasize topics: " + ", ".join(ctx.interests) + "."

    loc = f"in {ctx.location}" if ctx.location else ""
    ctype = f" reviewing a {ctx.contract_type}" if ctx.contract_type else ""

    # Guardrails to reduce hallucinations and constrain outputs
    guardrails = (
        "Guardrails:\n"
        "- Do not invent jurisdiction-specific numbers, limits, deadlines, or case names; "
        "state them only if they appear in 'Contextual hints'.\n"
        "- If the hints do not contain a specific number or rule, write: "
        "'Specific limits vary by jurisdiction—verify locally.'\n"
        "- If the clause text is too vague to be certain, say what is unclear and suggest confirming with a professional.\n"
        "- Do not fabricate sources or citations; avoid quoting nonexistent statutes.\n"
        "- Keep the answer aligned to the selected tone and begin exactly with: \"For you, this means…\""
    )

    hints_block = ""
    if hints:
        hints_joined = "\n- " + "\n- ".join(hints)
        hints_block = f"\nContextual hints:\n{hints_joined}\n"

    return (
        f"You are advising a {ctx.role} {loc}{ctype}.\n"
        f"{tone_line} {interests_line}\n"
        f"{guardrails}\n"
        f"{hints_block}"
        f'Here is the clause:\n"""{clause_text}"""\n'
        f'Start the answer with: "For you, this means…" and then explain.'
    )