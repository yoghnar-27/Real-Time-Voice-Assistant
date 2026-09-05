import os
from dotenv import load_dotenv
from google import genai
from app.tools.basic_tools import get_time, save_note

load_dotenv()


def ask_gemini(transcript: str) -> str:
    """Send one final transcript to Gemini and return its text response."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        contents=transcript,
        config={
            "system_instruction": (
                "You are a helpful voice assistant. Keep replies short and natural. "
                "Use a tool when the user's request matches one."
            ),
            "tools": [get_time, save_note],
        },
    )

    return response.text or "I could not generate a response."