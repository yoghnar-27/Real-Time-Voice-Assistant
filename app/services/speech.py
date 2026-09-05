import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()


def create_deepgram_client():
    """Create a Deepgram client when the API key is available."""
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPGRAM_API_KEY is missing")
    return DeepgramClient(api_key=api_key)


def get_final_transcript(result) -> str:
    """Read a final transcript from a Deepgram result."""
    if not getattr(result, "is_final", False):
        return ""

    channel = getattr(result, "channel", None)
    alternatives = getattr(channel, "alternatives", []) if channel else []
    if not alternatives:
        return ""
    return getattr(alternatives[0], "transcript", "") or ""