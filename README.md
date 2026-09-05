# Real-Time Voice Assistant

## Architecture

Browser microphone audio is sent over a WebSocket to FastAPI. FastAPI sends
the audio to Deepgram streaming speech-to-text, sends each final transcript to
Gemini, and returns the transcript and Gemini response to the browser.

## Run

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add the API keys.
4. Start the server with `uvicorn app.main:app --reload`.
5. Open `http://127.0.0.1:8000` and allow microphone access.

## Environment variables

`GEMINI_API_KEY` and `DEEPGRAM_API_KEY` are required. `GEMINI_MODEL` is
optional and defaults to `gemini-3.6-flash`. `ELEVENLABS_API_KEY` is reserved
for the future text-to-speech step.

## Current functionality

The assistant streams microphone audio to Deepgram, sends final transcripts to
Gemini, and displays Gemini replies. Gemini can use `get_time` and `save_note`.
Notes are stored only in memory while the server is running.

## Pending

ElevenLabs streaming text-to-speech has not been added yet.
