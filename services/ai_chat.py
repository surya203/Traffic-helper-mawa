import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = (
    "You are Traffic Advisor Mawa, a friendly Indian traffic instructor. "
    "Answer questions about roads, driving, and safety in plain, simple English. "
    "Keep answers short (3–6 sentences) unless the user asks for detail. "
    "When unsure, say so and suggest checking local signs or traffic police."
)


def ask_traffic_bot(user_message: str, history: list[dict] | None = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY is missing. Add it to your .env file and restart the app."

    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=512,
    )
    return response.choices[0].message.content
