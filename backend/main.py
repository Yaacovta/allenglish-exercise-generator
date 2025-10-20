# main.py
from openai_service import send_to_openai
import re

# ---------- Level & Type profiles ----------


def _level_profile(level: str) -> str:
    profiles = {
        "A1": (
            "Vocabulary: very basic everyday words. "
            "Sentences: very short and simple (5–8 words). "
            "Tenses: present simple; avoid complex clauses; no passive."
        ),
        "A2": (
            "Vocabulary: basic everyday with simple time words. "
            "Sentences: short (8–12 words). "
            "Tenses: present simple/past simple; limited adjectives; no conditionals."
        ),
        "B1": (
            "Vocabulary: common academic and daily-life words. "
            "Sentences: medium length (10–16 words). "
            "Tenses: present/past/simple future; some connectors (because/so/but)."
        ),
        "B2": (
            "Vocabulary: upper-intermediate; use paraphrase when needed. "
            "Sentences: medium-long (12–20 words). "
            "Tenses: mix of present, past, present perfect; clear cohesion."
        ),
    }
    return profiles.get(level, profiles["B1"])


def _type_spec(quiz_type: str) -> str:
    qt = quiz_type.lower()
    if qt == "grammar":
        return (
            "Create exactly 6 questions:\n"
            "• Q1–Q3: Multiple-choice (A–D) focusing on target grammar or tenses.\n"
            "• Q4–Q6: Fill-in-the-blank (e.g., 'He (go) to school ____.').\n"
            "Ensure only ONE correct answer per question."
        )
    if qt == "reading":
        return (
            "Create exactly 6 questions based on the source ideas (paraphrased):\n"
            "• Q1–Q4: Reading comprehension (who/what/when/where/why/how).\n"
            "• Q5–Q6: Vocabulary-in-context (synonym/meaning) with options A–D."
        )
    # vocabulary (default)
    return (
        "Create exactly 6 questions focusing on vocabulary:\n"
        "• At least 3 multiple-choice (A–D) for meaning/synonym/collocation.\n"
        "• The rest may be matching (word → definition) or fill-in-the-blank."
    )


def _system_prompt(level: str, quiz_type: str) -> str:
    return (
        "You are an expert English teacher assistant who generates classroom-ready exercises.\n"
        f"CEFR level: {level}. Exercise type: {quiz_type}.\n"
        "OUTPUT RULES (MANDATORY):\n"
        "- Plain text ONLY (no Markdown, no **bold**, no bullets).\n"
        "- Do NOT copy the source text verbatim; paraphrase ideas.\n"
        "- Begin with a header line: 'Level: <A1/A2/B1/B2> | Type: <Reading/Grammar/Vocabulary> Exercise'.\n"
        "- Provide Title and short Instructions (1–2 sentences).\n"
        "- Number questions 1.–6. (exactly six questions).\n"
        "- Multiple-choice options must be formatted as: A) ..., B) ..., C) ..., D) ...\n"
        "- Finish with a section titled exactly: ANSWER KEY (on its own line), then six lines like '1) B'.\n"
        f"- Level profile to respect: {_level_profile(level)}"
    )


def _user_prompt(source_text: str, level: str, quiz_type: str) -> str:
    return (
        f"### HEADER ###\n"
        f"Level: {level} | Type: {quiz_type.capitalize()} Exercise\n\n"
        "### TASK ###\n"
        "Use the source ideas below (do NOT copy sentences) to create an exercise.\n"
        "Provide a clear title and short instructions, then six numbered questions and an ANSWER KEY.\n\n"
        "SOURCE TEXT:\n"
        f"{source_text}\n\n"
        "TYPE SPEC:\n"
        f"{_type_spec(quiz_type)}\n\n"
        "OUTPUT FORMAT (STRICT):\n"
        "Title: <short title>\n"
        "Instructions: <1–2 sentences>\n"
        "1. <question>\n"
        "2. <question>\n"
        "3. <question>\n"
        "4. <question>\n"
        "5. <question>\n"
        "6. <question>\n"
        "ANSWER KEY\n"
        "1) <A/B/C/D or short answer>\n"
        "2) <...>\n"
        "3) <...>\n"
        "4) <...>\n"
        "5) <...>\n"
        "6) <...>\n"
    )


# ---------- Helpers for chat context ----------

_HDR_RE = re.compile(
    r"^\s*Level:\s*(A1|A2|B1|B2)\s*\|\s*Type:\s*([A-Za-z]+)",
    re.IGNORECASE | re.MULTILINE,
)


def _extract_header_meta(quiz_text: str) -> tuple[str, str]:
    """
    Extracts (level, type) from a line like:
    'Level: B1 | Type: Reading Exercise'
    Falls back to (B1, reading) if not found.
    """
    m = _HDR_RE.search(quiz_text or "")
    if not m:
        return ("B1", "reading")
    level = m.group(1).upper()
    qtype = m.group(2).strip().lower()
    # normalize e.g. 'Reading' / 'ReadingExercise' → 'reading'
    qtype = qtype.split()[0]
    return (level, qtype)


# ---------- Public flows ----------

async def create_quiz_flow(source_text: str, level: str, quiz_type: str) -> str:
    """
    Generates a consistent quiz with clear header and structure.
    """
    messages = [
        {"role": "system", "content": _system_prompt(level, quiz_type)},
        {"role": "user", "content": _user_prompt(source_text, level, quiz_type)},
    ]
    return send_to_openai(messages)


async def chat_edit_flow(quiz_text: str, message: str) -> str:
    """
    Applies MINIMAL edits to the existing quiz, with full context:
    - Preserves header (Level/Type), Title, Instructions, Q1–Q6, ANSWER KEY.
    - Keeps any part UNCHANGED VERBATIM unless the request requires a modification.
    - Maintains CEFR level and exercise type extracted from the current header.
    - Returns the FULL revised quiz in the same strict format.
    """
    level, quiz_type = _extract_header_meta(quiz_text)

    system = (
        "You are an assistant that REVISES an existing English exercise.\n"
        "HARD REQUIREMENTS:\n"
        "1) Do MINIMAL necessary changes to satisfy the user's request. Do NOT rewrite the whole quiz.\n"
        "2) PRESERVE the overall format EXACTLY:\n"
        "   - First line (header): 'Level: <A1/A2/B1/B2> | Type: <Reading/Grammar/Vocabulary> Exercise'\n"
        "   - Then: Title, Instructions, numbered questions 1–6 (exactly six), then 'ANSWER KEY' on its own line with six lines '1) ...' to '6) ...'.\n"
        "3) Keep any text that is not directly affected by the request VERBATIM (unchanged).\n"
        "4) If a question becomes multiple-choice, format options exactly: A) ..., B) ..., C) ..., D) ... with ONE correct answer.\n"
        "5) No Markdown, no explanations.\n"
        f"6) Keep CEFR level = {level} and exercise type = {quiz_type}.\n"
    )

    user = (
        "CURRENT QUIZ (preserve structure and all unchanged lines verbatim):\n"
        f"{quiz_text}\n\n"
        "EDIT REQUEST (apply only what is necessary; if ambiguous, choose the smallest change that satisfies it):\n"
        f"{message}\n\n"
        "Return the FULL revised quiz in the SAME format (header + title + instructions + questions 1–6 + ANSWER KEY)."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    return send_to_openai(messages)
