import os

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()


def text_to_speech(text: str) -> bytes:
    """Convert assistant text into MP3 audio bytes."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is missing")

    client = ElevenLabs(api_key=api_key)
    audio_chunks = client.text_to_speech.convert(
        voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
        text=text,
        model_id=os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        output_format="mp3_44100_128",
    )
    return b"".join(audio_chunks)