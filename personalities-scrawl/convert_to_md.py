#!/usr/bin/env python3
"""Convert personalities.json to a psychologist-oriented markdown file.

Usage:
    python convert_to_md.py
Outputs:
    ../make-psychologist/research-takeaways/MBTI 16 Personality Types.md
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
JSON_PATH = HERE / "personalities.json"
OUT_PATH = HERE.parent / "make-psychologist" / "research-takeaways" / "MBTI 16 Personality Types.md"

ROLE_GUIDANCE = {
    "analyst": (
        "Lead with logic and evidence — this type respects intellectual rigour over emotional appeals. "
        "Frame advice as hypotheses to test, not prescriptions to follow. "
        "Engage their curiosity by exploring root causes and systemic patterns. "
        "Avoid excessive small talk; get to the substance. "
        "Acknowledge the complexity of their situation before offering frameworks."
    ),
    "diplomat": (
        "Open with genuine empathy and validate their feelings before moving to insight. "
        "Connect advice to their values and sense of purpose — they are motivated by meaning, not just outcomes. "
        "Ask what matters most to them before suggesting a path forward. "
        "Avoid cold, purely analytical framing; honour the emotional dimension. "
        "Invite them to reflect on how their goals align with who they truly want to be."
    ),
    "sentinel": (
        "Respect structure: offer clear, step-by-step guidance rather than open-ended exploration. "
        "Acknowledge their reliability and conscientiousness before naming blind spots. "
        "Ground advice in practical, proven approaches rather than experimental ideas. "
        "Be direct and concrete — they value clarity and follow-through. "
        "Validate their need for stability while gently expanding their comfort with change."
    ),
    "explorer": (
        "Keep sessions dynamic and concrete; avoid lengthy abstract theory. "
        "Respect their autonomy — frame guidance as options they choose, not rules to follow. "
        "Tie insights to immediate, tangible action they can take today. "
        "Match their energy and be willing to explore tangents that feel alive to them. "
        "Acknowledge their adaptability as a strength before addressing follow-through challenges."
    ),
}


def format_personality(p: dict) -> str:
    type_code = p["type_code"]
    nickname = p["nickname"]
    role = p["role"]
    definition = p["definition"]
    strengths = p["strengths"]
    weaknesses = p["weaknesses"]
    description_paragraphs = p.get("description_paragraphs", [])
    key_quotes = p.get("key_quotes", [])

    # Use first two substantive description paragraphs (skip quotes)
    desc_text = [para for para in description_paragraphs if not para.startswith('"') and len(para) > 80]
    core_desc = " ".join(desc_text[:2]) if desc_text else ""

    strengths_lines = "\n".join(f"- {s['name']}: {s['description']}" for s in strengths)
    weaknesses_lines = "\n".join(f"- {w['name']}: {w['description']}" for w in weaknesses)
    quotes_lines = ("\n" + "\n".join(f'> "{q}"' for q in key_quotes)) if key_quotes else ""

    guidance = ROLE_GUIDANCE.get(role, "")

    section = f"""**{type_code} – {nickname} ({role.capitalize()})**

{definition}

{core_desc}
{quotes_lines}

Strengths to leverage in coaching:
{strengths_lines}

Challenges and blind spots to navigate:
{weaknesses_lines}

Working with this type:
{guidance}
"""
    return section.strip()


def main() -> None:
    personalities = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    header = """# MBTI 16 Personality Types — Psychologist Reference Guide

This guide covers all 16 MBTI personality types organised into four groups:
- **Analysts** (INTJ, INTP, ENTJ, ENTP): Rational, strategic, logic-driven
- **Diplomats** (INFJ, INFP, ENFJ, ENFP): Empathic, idealistic, values-driven
- **Sentinels** (ISTJ, ISFJ, ESTJ, ESFJ): Practical, dutiful, stability-oriented
- **Explorers** (ISTP, ISFP, ESTP, ESFP): Spontaneous, adaptable, action-oriented

Each section describes the type's core traits, strengths, challenges, and guidance for effective psychologist communication.

"""

    sections = [format_personality(p) for p in personalities]
    content = header + "\n\n---\n\n".join(sections) + "\n"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(content, encoding="utf-8")
    print(f"Written {len(personalities)} personality profiles to:\n  {OUT_PATH}")


if __name__ == "__main__":
    main()
