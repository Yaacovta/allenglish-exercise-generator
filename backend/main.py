# main.py
import asyncio
import random
import re

from openai_service import send_to_openai

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
        "C1": (
            "Vocabulary: advanced and nuanced, including idiomatic expressions, collocations and abstract or academic topics. "
            "Sentences: long and varied (15–25 words), complex clauses and nominalisation. "
            "Tenses: full range including mixed conditionals, inversion, cleft sentences, subjunctive and advanced passive structures."
        ),
        "C2": (
            "Vocabulary: sophisticated and precise, including rare words, subtle shades of meaning, figurative language and register differences. "
            "Sentences: sophisticated, with dense structure and implicit meaning. "
            "Tenses: complete mastery, including stylistic variation, ellipsis and complex discourse markers."
        ),
    }
    return profiles.get(level.upper(), profiles["B1"])


# Required grammar topics per level (used only for Grammar quizzes)
GRAMMAR_FOCUS = {
    "B2": ["Modal Verbs"],
    "C1": [
        "Infinitive",
        "Gerund",
        "Participle I (present participle)",
        "Participle II (past participle)",
    ],
}


def _type_spec(quiz_type: str, level: str = "B1") -> str:
    qt = (quiz_type or "").strip().lower()
    if qt == "reading":
        return (
            "Reading comprehension: each question checks understanding of its segment (main idea, details or inference).\n"
            "Paraphrase; do not quote sentences."
        )
    if qt == "grammar":
        topics = GRAMMAR_FOCUS.get((level or "").upper())
        if topics:
            return (
                "Grammar: every question must test one of these REQUIRED grammar topics: "
                + "; ".join(topics) + ".\n"
                "Spread the questions as evenly as possible across the topics, "
                "so each topic appears at least once when the number of questions allows it.\n"
                "Use the segment for context and vocabulary where possible, "
                "but the required topics take priority over the grammar found in the text.\n"
                "Use multiple-choice or fill-in-the-blank, with sentences suited to the level."
            )
        return (
            "Grammar: target a clear grammar point found in the segment.\n"
            "Use multiple-choice or fill-in-the-blank, with sentences suited to the level."
        )
    if qt == "vocabulary":
        return (
            "Vocabulary: focus on the meaning, synonyms or context usage of a word or phrase from the segment.\n"
            "Use multiple-choice matching (word → definition) or fill-in-the-blank."
        )
    if qt == "truefalse":
        return (
            "True/False: create a statement based on the segment (paraphrased).\n"
            "Each statement must be clearly TRUE or clearly FALSE based on the segment."
        )
    return "General English exercise."


def _system_prompt(level: str, quiz_type: str, question_count: int) -> str:
    tf_rule = (
        "- True/False: after EVERY statement write its two options on separate lines, exactly: "
        "A) True and B) False. Never leave the options out.\n"
        if quiz_type.lower() == "truefalse"
        else "- Multiple-choice options must be formatted as: A) ..., B) ..., C) ..., D) ...\n"
    )

    return (
        "You are an expert English teacher assistant who generates classroom-ready exercises.\n"
        f"CEFR level: {level}. Exercise type: {quiz_type}.\n"
        "OUTPUT RULES (MANDATORY):\n"
        "- Plain text ONLY (no Markdown, no **bold**, no bullets).\n"
        "- Do NOT copy the source text verbatim; paraphrase ideas.\n"
        "- Begin with a header line: 'Level: <A1/A2/B1/B2/C1/C2> | Type: <Reading/Grammar/Vocabulary/TrueFalse> Exercise'.\n"
        "- Provide Title and short Instructions (1–2 sentences).\n"
        f"- Number questions 1.–{question_count}. (exactly {question_count} questions).\n"
        "- SEGMENTS (MANDATORY): the user message gives numbered source segments. Write exactly one question per segment, "
        "in the same order: question 1 uses ONLY Segment 1, question 2 uses ONLY Segment 2, and so on. "
        "Never use ideas from a different segment. "
        "The student will NOT see the segments: never write the word 'Segment' or a segment number "
        "inside a question or an option (write 'the text' or 'the passage' if you must refer to it).\n"
        f"{tf_rule}"
        f"- Finish with a section titled exactly: ANSWER KEY (on its own line), then {question_count} lines like '1) B'.\n"
        f"- Level profile to respect: {_level_profile(level)}"
    )


# ---------- Helpers for chat context ----------

_HDR_RE = re.compile(
    r"^\s*Level:\s*(A1|A2|B1|B2|C1|C2)\s*\|\s*Type:\s*([A-Za-z]+)",
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


# ---------- Source text: splitting into ordered segments ----------

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_into_segments(text: str, n: int) -> list:
    """
    Splits the source text into n consecutive segments, in text order.
    - If the text has at least n paragraphs, whole paragraphs are grouped (never cut in the middle).
    - Otherwise the text is split by sentences.
    - If there are fewer sentences than n, neighbouring questions share a sentence (order is kept).
    """
    paragraphs = [p.strip() for p in (text or "").replace("\r\n", "\n").split("\n") if p.strip()]
    if not paragraphs:
        return [(text or "").strip()] * n

    units = paragraphs
    if len(units) < n:
        units = []
        for para in paragraphs:
            units.extend(s.strip() for s in _SENT_SPLIT_RE.split(para) if s.strip())

    total = len(units)
    segments = []
    if total >= n:
        base, extra = divmod(total, n)
        start = 0
        for i in range(n):
            size = base + (1 if i < extra else 0)
            segments.append(" ".join(units[start:start + size]))
            start += size
    else:
        for i in range(n):
            segments.append(units[min(total - 1, i * total // n)])
    return segments


def _user_prompt(segments: list, level: str, quiz_type: str) -> str:
    question_count = len(segments)
    type_name = _display_type_name(quiz_type)

    segments_block = "\n\n".join(f"Segment {i}:\n{s}" for i, s in enumerate(segments, start=1))
    if (quiz_type or "").strip().lower() == "truefalse":
        questions_block = "\n".join(
            [f"{i}. <statement based on Segment {i}>\nA) True\nB) False" for i in range(1, question_count + 1)]
        )
    else:
        questions_block = "\n".join([f"{i}. <question about Segment {i}>" for i in range(1, question_count + 1)])
    answer_key_block = "\n".join([f"{i}) <A/B/C/D or short answer>" for i in range(1, question_count + 1)])

    return (
        "### HEADER ###\n"
        f"Level: {level} | Type: {type_name} Exercise\n\n"
        "### TASK ###\n"
        "Use the source segments below (do NOT copy sentences) to create an exercise.\n"
        f"Write EXACTLY {question_count} numbered questions: one question for each segment, in the same order. "
        "Question 1 must be based ONLY on Segment 1, question 2 ONLY on Segment 2, and so on. "
        "Never use ideas from a different segment.\n"
        "The student will NOT see the segments or their numbers: never write the word 'Segment' "
        "or a segment number inside a question or an option.\n"
        "Provide a clear title and short instructions, then the questions and an ANSWER KEY.\n\n"
        "SOURCE SEGMENTS (in the order they appear in the text):\n"
        f"{segments_block}\n\n"
        "TYPE SPEC:\n"
        f"{_type_spec(quiz_type, level)}\n\n"
        "OUTPUT FORMAT (STRICT):\n"
        "Title: <short title>\n"
        "Instructions: <1–2 sentences>\n"
        f"{questions_block}\n"
        "ANSWER KEY\n"
        f"{answer_key_block}\n"
    )


# ---------- Parsing one generated part ----------

_PART_NAMES = {
    "reading": "Reading Comprehension",
    "grammar": "Grammar",
    "vocabulary": "Vocabulary",
    "truefalse": "True / False",
}

_Q_START_RE = re.compile(r"^\s*(\d+)\s*\.\s+(.*)$")
_ANS_RE = re.compile(r"^\s*(\d+)\s*[).:\-]\s*(.+?)\s*$")


def _answer_key_index(lines: list) -> int:
    for i, line in enumerate(lines):
        cleaned = re.sub(r"[*_`~#>]", "", line).strip().lower()
        if cleaned.startswith("answer key"):
            return i
    return len(lines)


def _parse_section(text: str) -> dict:
    """
    Splits one generated part into title, instructions, questions (without numbers) and answers.
    """
    lines = (text or "").replace("\r\n", "\n").split("\n")

    key_idx = _answer_key_index(lines)
    body, key_lines = lines[:key_idx], lines[key_idx + 1:]

    title = ""
    instructions = ""
    for line in body:
        m = re.match(r"^\s*Title:\s*(.+)$", line, flags=re.IGNORECASE)
        if m and not title:
            title = m.group(1).strip()
        m = re.match(r"^\s*Instructions:\s*(.+)$", line, flags=re.IGNORECASE)
        if m and not instructions:
            instructions = m.group(1).strip()

    blocks = []
    current = None
    for line in body:
        m = _Q_START_RE.match(line)
        if m:
            current = [m.group(2).strip()]
            blocks.append(current)
        elif current is not None:
            current.append(line.rstrip())

    questions = []
    for block in blocks:
        while block and not block[-1].strip():
            block.pop()
        questions.append("\n".join(block))

    answers_by_number = {}
    for line in key_lines:
        m = _ANS_RE.match(line)
        if m:
            answers_by_number[int(m.group(1))] = m.group(2).strip()

    return {
        "title": title,
        "instructions": instructions,
        "questions": questions,
        "answers": [answers_by_number.get(i, "?") for i in range(1, len(questions) + 1)],
    }


# ---------- Safety nets applied to every generated question ----------

_SEG_LEADING_RE = re.compile(
    r"^(?:in|from|according to|based on|within|looking at|refer to)\s+(?:the\s+)?segment\s*\d+\s*[,:]?\s*",
    re.IGNORECASE,
)
_SEG_PHRASE_RE = re.compile(
    r"\s*,?\s*\b(?:in|from|of|within|according to|based on)\s+(?:the\s+context\s+of\s+)?(?:the\s+)?segments?\s*\d+\b",
    re.IGNORECASE,
)
_SEG_ANY_RE = re.compile(r"\bsegments?\s*\d+\b", re.IGNORECASE)
_HAS_OPTION_A_RE = re.compile(r"^\s*\(?A\)?[.)]\s+", re.MULTILINE)


def _clean_segment_mentions(question: str) -> str:
    """The word 'Segment' is internal; students must never see it."""
    lines = question.split("\n")
    lines[0] = _SEG_LEADING_RE.sub("", lines[0])
    text = "\n".join(lines)
    text = _SEG_PHRASE_RE.sub("", text)
    text = _SEG_ANY_RE.sub("the text", text)
    text = text.strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def _ensure_tf_options(question: str) -> str:
    """True/False questions must always show the options A) True and B) False."""
    if _HAS_OPTION_A_RE.search(question):
        return question
    return f"{question}\nA) True\nB) False"


def _normalize_tf_answer(answer: str) -> str:
    """If the model wrote 'True'/'False' in the answer key, turn it into the option letter."""
    cleaned = re.sub(r"[^a-z]", "", (answer or "").lower())
    if cleaned in ("true", "t"):
        return "A"
    if cleaned in ("false", "f"):
        return "B"
    return answer


def _finalize_question(quiz_type: str, question: str, answer: str) -> tuple:
    question = _clean_segment_mentions(question)
    if quiz_type == "truefalse":
        question = _ensure_tf_options(question)
        answer = _normalize_tf_answer(answer)
    return question, answer


# ---------- Building the final quiz ----------

def _build_quiz(level: str, items: list, sections: list, single_parsed: dict | None) -> str:
    """
    items: list of (question, answer) already in text order.
    sections: list of (quiz_type, count) as chosen by the teacher.
    single_parsed: parsed output when the quiz has only one type (to keep the AI's title/instructions).
    """
    if len(sections) == 1:
        quiz_type = sections[0][0]
        type_name = _display_type_name(quiz_type)
        title = (single_parsed or {}).get("title") or f"{type_name} Exercise"
        instructions = (single_parsed or {}).get("instructions") or "Choose the correct answer for each question."
    else:
        type_name = "Mixed"
        names = ", ".join(_PART_NAMES.get(t, t) for t, _ in sections)
        title = f"Mixed English Quiz ({names})"
        instructions = "Answer all the questions in order. Choose the correct option where choices are given."

    out = [
        f"Level: {level} | Type: {type_name} Exercise",
        f"Title: {title}",
        f"Instructions: {instructions}",
        "",
    ]
    answers_out = []
    for n, (q, a) in enumerate(items, start=1):
        out.append(f"{n}. {q}")
        out.append("")
        answers_out.append(f"{n}) {a}")

    out.append("ANSWER KEY")
    out.extend(answers_out)
    return "\n".join(out)


# ---------- Public flows ----------

async def _create_single_quiz(segments: list, level: str, quiz_type: str) -> str:
    """
    Generates the questions of ONE type, one per given segment.
    Runs in a thread so several types can be generated in parallel.
    """
    messages = [
        {"role": "system", "content": _system_prompt(level, quiz_type, len(segments))},
        {"role": "user", "content": _user_prompt(segments, level, quiz_type)},
    ]
    return await asyncio.to_thread(send_to_openai, messages)


async def create_quiz_flow(source_text: str, level: str, sections: list) -> str:
    """
    sections: list of (quiz_type, question_count), e.g. [("reading", 2), ("grammar", 2), ("vocabulary", 1)]

    How the order is guaranteed:
    1. The teacher's choices become a list of question slots (one slot per question).
    2. The types are assigned to the slots at random.
    3. The text is split into as many consecutive segments as there are slots, in text order.
    4. Slot i always gets segment i, so the quiz follows the text no matter which type each slot got.
    """
    types_sequence = [t for t, count in sections for _ in range(count)]
    random.shuffle(types_sequence)
    total = len(types_sequence)
    segments = _split_into_segments(source_text, total)

    async def build_part(quiz_type: str):
        slots = [i for i, t in enumerate(types_sequence) if t == quiz_type]
        raw = await _create_single_quiz([segments[i] for i in slots], level, quiz_type)
        return quiz_type, slots, raw, _parse_section(raw)

    results = await asyncio.gather(*(build_part(t) for t, _ in sections))

    slot_items = {}
    for quiz_type, slots, raw, parsed in results:
        if not parsed["questions"]:
            if len(results) == 1:
                # Could not parse the output: return it as is
                return raw
            name = _PART_NAMES.get(quiz_type, quiz_type)
            raise ValueError(f"The AI returned no questions for the {name} part. Please try again.")
        for slot, q, a in zip(slots, parsed["questions"], parsed["answers"]):
            slot_items[slot] = _finalize_question(quiz_type, q, a)

    items = [slot_items[i] for i in sorted(slot_items)]
    single_parsed = results[0][3] if len(results) == 1 else None
    return _build_quiz(level, items, sections, single_parsed)


# ---------- Unseen: a text from the teacher's description, then the quiz ----------

_PARAGRAPH_GUIDE = {
    "A1": "2 very short and simple sentences",
    "A2": "2–3 short sentences",
    "B1": "3–4 sentences",
    "B2": "3–5 sentences",
    "C1": "4–6 sentences",
    "C2": "4–6 rich, complex sentences",
}


def _passage_messages(description: str, level: str, paragraphs: int) -> list:
    guide = _PARAGRAPH_GUIDE.get(level.upper(), _PARAGRAPH_GUIDE["B1"])
    system = (
        "You are an expert English teacher who writes reading passages for students.\n"
        f"CEFR level: {level}.\n"
        "RULES (MANDATORY):\n"
        "- Plain text ONLY (no Markdown, no bullets, no bold).\n"
        "- Write ONE coherent, engaging, educational text, based on the teacher's description. "
        "It must develop logically from the beginning to the end.\n"
        f"- Exactly {paragraphs} paragraphs, separated by one blank line. Each paragraph: {guide}.\n"
        "- Each paragraph must be understandable on its own and cover its own part of the topic or story, "
        "so that a question can be written about each paragraph.\n"
        "- Do not number the paragraphs. Do not add questions, notes or explanations.\n"
        "- Keep the content appropriate for school students.\n"
        f"- Level profile to respect: {_level_profile(level)}\n"
        "OUTPUT FORMAT: the first line is 'Title: <short title>', then a blank line, then the paragraphs."
    )
    user = f"TEACHER'S DESCRIPTION:\n{description}\n\nWrite the text now."
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _parse_passage(raw: str) -> tuple:
    """Returns (title, passage). The passage keeps one blank line between paragraphs."""
    lines = (raw or "").replace("\r\n", "\n").strip().split("\n")
    title = ""
    if lines and re.match(r"^\s*Title:\s*", lines[0], flags=re.IGNORECASE):
        title = re.sub(r"^\s*Title:\s*", "", lines[0], flags=re.IGNORECASE).strip()
        lines = lines[1:]

    paragraphs = []
    for line in lines:
        text = re.sub(r"[*_`~#>]", "", line).strip()
        text = re.sub(r"^(?:paragraph\s*\d+\s*[:.)\-]\s*)", "", text, flags=re.IGNORECASE)
        if text:
            paragraphs.append(text)
    return title, "\n\n".join(paragraphs)


async def generate_passage_flow(description: str, level: str, paragraphs: int) -> tuple:
    messages = _passage_messages(description, level, paragraphs)
    # More room for the answer (a full text) and a little more variety than for quiz questions
    raw = await asyncio.to_thread(send_to_openai, messages, 2500, 0.7)
    title, passage = _parse_passage(raw)
    if not passage:
        raise ValueError("The AI could not write the text. Please try again.")
    return title, passage


async def create_unseen_flow(description: str, level: str, sections: list) -> tuple:
    """
    sections: list of (quiz_type, question_count), same as create_quiz_flow.
    1. The AI writes a text from the teacher's description, with about one paragraph per question.
    2. The quiz is created from that text (the same flow used for a pasted text).
    Returns (title, passage, quiz_text).
    """
    total = sum(count for _, count in sections)
    paragraphs = max(3, min(8, total))
    title, passage = await generate_passage_flow(description, level, paragraphs)
    quiz_text = await create_quiz_flow(passage, level, sections)
    return title, passage, quiz_text


async def chat_edit_flow(quiz_text: str, message: str) -> str:
    """
    Applies MINIMAL edits to the existing quiz, preserving structure and formatting.
    """
    level, quiz_type = _extract_header_meta(quiz_text)
    question_count = _infer_question_count(quiz_text)

    if quiz_type.lower() == "truefalse":
        tf_rule = "4) If a question is True/False, format options exactly as: A) True, B) False with ONE correct answer.\n"
    elif quiz_type.lower() == "mixed":
        tf_rule = (
            "4) Keep each question's options formatted as it is now: True/False questions use A) True, B) False; "
            "multiple-choice questions use A) ..., B) ..., C) ..., D) ...; each with ONE correct answer.\n"
        )
    else:
        tf_rule = "4) If a question is multiple-choice, format options exactly: A) ..., B) ..., C) ..., D) ... with ONE correct answer.\n"

    system = (
        "You are an assistant that REVISES an existing English exercise.\n"
        "HARD REQUIREMENTS:\n"
        "1) Do MINIMAL necessary changes to satisfy the user's request. Do NOT rewrite the whole quiz.\n"
        "2) PRESERVE the overall format EXACTLY:\n"
        "   - First line (header): 'Level: <A1/A2/B1/B2/C1/C2> | Type: <Reading/Grammar/Vocabulary/TrueFalse/Mixed> Exercise'\n"
        f"   - Then: Title, Instructions, numbered questions 1–{question_count} (exactly {question_count}), then 'ANSWER KEY' on its own line with {question_count} lines '1) ...' to '{question_count}) ...'.\n"
        "3) Keep any text that is not directly affected by the request VERBATIM (unchanged). "
        "Keep the questions in their current order (the order follows the source text) unless the user asks to change it.\n"
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