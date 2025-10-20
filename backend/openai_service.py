from openai import OpenAI
import os
from typing import List, Dict


# Set the OpenAI API key using an environment variable
OpenAI.api_key = os.getenv("OPENAI_API_KEY")


def send_to_openai(conversation_history: List[Dict[str, str]]) -> str:

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        max_tokens=800,
        temperature=0.3

    )
    return completion.choices[0].message.content.strip()
