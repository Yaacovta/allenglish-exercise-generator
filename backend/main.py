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
            "Vocabulary: common daily topics. "
            "Sentences: short and simple (7–12 words). "
            "Tenses: present simple + past simple; limited connectors (and/but/because)."
        ),
        "B1": (
            "Vocabulary: everyday + school/work topics. "
            "Sentences: medium length (10–16 words), allow some clauses. "
            "Tenses: present/past/future; modals (can/should); simple passive acceptable."
        ),
        "B2": (
            "Vocabulary: wider range, abstract topics allowed. "
            "Sentences: varied length; more complex structures. "
            "Tenses: full range; conditionals; passive voice; more advanced connectors."
        ),
    }
    return profiles.get(level.upper(), profiles["B1"])


def _type_spec(quiz_type: str) -> str:
    qt = (quiz_type or "").strip().lower()
    if qt == "reading":
        return (
            "Reading comprehension: questions should check understanding of main ideas, details, inference.\n"
            "Keep questions aligned to the text and paraphrase (do not quote sentences)."
        )
    if qt == "grammar":
        return (
            "Grammar: target a clear grammar point inferred from the text.\n"
            "Use short sentences and ask multiple-choice or fill-in-the-blank."
        )
    if qt == "vocabulary":
        return (
            "Vocabulary: focus on word meanings, synonyms, context usage.\n"
            "Use multiple-choice matching (word → definition) or fill-in-the-blank."
        )
    if qt == "truefalse":
        return (
            "True/False: create statements based on the source ideas (paraphrased).\n"
            "Each statement must be clearly TRUE or clearly FALSE based on the text ideas."
        )
    return "General English exercise."


def _system_prompt(level: str, quiz_type: str, question_count: int) -> str:
    tf_rule = (
        "- True/False options must be formatted exactly as: A) True, B) False\n"
        if quiz_type.lower() == "truefalse"
        else "- Multiple-choice options must be formatted as: A) ..., B) ..., C) ..., D) ...\n"
    )

    return (
        "You are an expert English teacher assistant who generates classroom-ready exercises.\n"
        f"CEFR level: {level}. Exercise type: {quiz_type}.\n"
        "OUTPUT RULES (MANDATORY):\n"
        "- Plain text ONLY (no Markdown, no **bold**, no bullets).\n"
        "- Do NOT copy the source text verbatim; paraphrase ideas.\n"
        "- Begin with a header line: 'Level: <A1/A2/B1/B2> | Type: <Reading/Grammar/Vocabulary/TrueFalse> Exercise'.\n"
        "- Provide Title and short Instructions (1–2 sentences).\n"
        f"- Number questions 1.–{question_count}. (exactly {question_count} questions).\n"
        f"{tf_rule}"
        f"- Finish with a section titled exactly: ANSWER KEY (on its own line), then {question_count} lines like '1) B'.\n"
        f"- Level profile to respect: {_level_profile(level)}"
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
    qtype = qtype.split()[0]
    return (level, qtype)


def _display_type_name(quiz_type: str) -> str:
    qt = (quiz_type or "").strip().lower()
    if qt == "reading":
        return "Reading"
    if qt == "grammar":
        return "Grammar"
    if qt == "vocabulary":
        return "Vocabulary"
    if qt == "truefalse":
        return "TrueFalse"
    return re.sub(r"[^A-Za-z]+", "", qt).title() or "Reading"


def _infer_question_count(quiz_text: str) -> int:
    """Infer how many numbered questions exist in the quiz text."""
    if not quiz_text:
        return 6
    nums = re.findall(r"^\s*(\d+)\s*\.", quiz_text, flags=re.MULTILINE)
    if not nums:
        return 6
    try:
        return max(int(n) for n in nums)
    except Exception:
        return len(nums) or 6


def _user_prompt(source_text: str, level: str, quiz_type: str, question_count: int) -> str:
    type_name = _display_type_name(quiz_type)

    questions_block = "\n".join([f"{i}. <question>" for i in range(1, question_count + 1)])
    answer_key_block = "\n".join([f"{i}) <A/B/C/D or short answer>" for i in range(1, question_count + 1)])

    return (
        "### HEADER ###\n"
        f"Level: {level} | Type: {type_name} Exercise\n\n"
        "### TASK ###\n"
        "Use the source ideas below (do NOT copy sentences) to create an exercise.\n"
        f"Provide a clear title and short instructions, then {question_count} numbered questions and an ANSWER KEY.\n\n"
        "SOURCE TEXT:\n"
        f"{source_text}\n\n"
        "TYPE SPEC:\n"
        f"{_type_spec(quiz_type)}\n\n"
        "OUTPUT FORMAT (STRICT):\n"
        "Title: <short title>\n"
        "Instructions: <1–2 sentences>\n"
        f"{questions_block}\n"
        "ANSWER KEY\n"
        f"{answer_key_block}\n"
    )


# ---------- Public flows ----------

async def create_quiz_flow(source_text: str, level: str, quiz_type: str, question_count: int) -> str:
    """
    Generates a consistent quiz with clear header and structure.
    """
    messages = [
        {"role": "system", "content": _system_prompt(level, quiz_type, question_count)},
        {"role": "user", "content": _user_prompt(source_text, level, quiz_type, question_count)},
    ]
    return send_to_openai(messages)


async def chat_edit_flow(quiz_text: str, message: str) -> str:
    """
    Applies MINIMAL edits to the existing quiz, preserving structure and formatting.
    """
    level, quiz_type = _extract_header_meta(quiz_text)
    question_count = _infer_question_count(quiz_text)

    tf_rule = (
        "4) If a question is True/False, format options exactly as: A) True, B) False with ONE correct answer.\n"
        if quiz_type.lower() == "truefalse"
        else "4) If a question is multiple-choice, format options exactly: A) ..., B) ..., C) ..., D) ... with ONE correct answer.\n"
    )

    system = (
        "You are an assistant that REVISES an existing English exercise.\n"
        "HARD REQUIREMENTS:\n"
        "1) Do MINIMAL necessary changes to satisfy the user's request. Do NOT rewrite the whole quiz.\n"
        "2) PRESERVE the overall format EXACTLY:\n"
        "   - First line (header): 'Level: <A1/A2/B1/B2> | Type: <Reading/Grammar/Vocabulary/TrueFalse> Exercise'\n"
        f"   - Then: Title, Instructions, numbered questions 1–{question_count} (exactly {question_count}), then 'ANSWER KEY' on its own line with {question_count} lines '1) ...' to '{question_count}) ...'.\n"
        "3) Keep any text that is not directly affected by the request VERBATIM (unchanged).\n"
        f"{tf_rule}"
        "5) No Markdown, no explanations.\n"
        f"6) Keep CEFR level = {level} and exercise type = {quiz_type}.\n"
    )

    user = (
        "CURRENT QUIZ (preserve structure and all unchanged lines verbatim):\n"
        f"{quiz_text}\n\n"
        "EDIT REQUEST (apply only what is necessary; if ambiguous, choose the smallest change that satisfies it):\n"
        f"{message}\n\n"
        f"Return the FULL revised quiz in the SAME format (header + title + instructions + questions 1–{question_count} + ANSWER KEY)."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return send_to_openai(messages)
