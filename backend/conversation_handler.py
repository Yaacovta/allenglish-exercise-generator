# conversation_handler.py
# Conversation manager for building/keeping a short chat history.

from __future__ import annotations
from typing import Dict, List

# Store conversations per session (key → list of messages)
_conversations: Dict[str, List[Dict[str, str]]] = {}

# Maximum messages in a single conversation (including the system message)
MAX_MESSAGES = 21


def initialize_conversation(
    session_id: str = "default",
    level: str = "B1",
    quiz_type: str = "reading",
) -> None:
    """
    Start a new conversation with a system message that defines the assistant role.
    The system message will never be deleted.
    """
    system_prompt = (
        "You are a creative English-teacher assistant. "
        f"Match CEFR level={level} and exercise type={quiz_type}. "
        "Always return PLAIN TEXT suitable for DOCX/PDF generation. "
        "If multiple-choice, provide 4 options (A–D) and only one correct answer. "
        "End with an ANSWER KEY."
    )
    _conversations[session_id] = [{"role": "system", "content": system_prompt}]


def add_message(session_id: str, role: str, content: str) -> None:
    """
    Append a message and enforce MAX_MESSAGES while keeping the system message.
    role ∈ {'user','assistant'}
    """
    if session_id not in _conversations:
        initialize_conversation(session_id)

    history = _conversations[session_id]
    history.append({"role": role, "content": content})

    # Enforce limit while not removing the first (system) message
    while len(history) > MAX_MESSAGES:
        # Remove the message right after the system message
        if len(history) > 1:
            history.pop(1)
        else:
            break


def get_conversation_history(session_id: str = "default") -> List[Dict[str, str]]:
    """Return the current conversation history list (mutable)."""
    return _conversations.get(session_id, [])
