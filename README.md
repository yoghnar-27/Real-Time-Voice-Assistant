# Real-Time Voice Assistant

## Project description

A beginner-friendly real-time voice assistant. The browser records microphone
audio, the backend transcribes it, Gemini generates a reply, and ElevenLabs
speaks the reply back through the browser.

## Architecture

Microphone -> WebSocket -> FastAPI -> Deepgram STT -> Gemini + tools ->
ElevenLabs TTS -> WebSocket -> Browser audio

## Technologies

HTML, CSS, JavaScript, Python, FastAPI, WebSockets, Deepgram, Gemini, and
ElevenLabs.

## Run

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and add the API keys.
4. Start the server with `uvicorn app.main:app --reload`.
5. Open `http://127.0.0.1:8000` and allow microphone access.

## Environment variables

`GEMINI_API_KEY`, `DEEPGRAM_API_KEY`, and `ELEVENLABS_API_KEY` are required.
`GEMINI_MODEL`, `ELEVENLABS_VOICE_ID`, and `ELEVENLABS_MODEL` are optional.

## Current functionality

The assistant streams microphone audio to Deepgram, sends final transcripts to
Gemini, displays Gemini replies, and plays ElevenLabs MP3 audio in the browser.
The Start and Stop buttons manage the microphone and WebSocket. Speaking while
audio is playing stops the current audio and continues listening.

Available tools are `get_time` and `save_note`. Notes are stored only in memory
while the server is running.

## Voice flow

1. Click Start and allow microphone access.
2. Speak into the microphone.
3. Deepgram returns a final transcript.
4. Gemini responds and may call a tool.
5. ElevenLabs converts the response to MP3 audio.
6. The browser plays the audio and keeps listening.

## Known limitations

ElevenLabs audio is generated as one MP3 response before playback rather than
being played chunk by chunk. The current ElevenLabs account must have API
access to a usable voice; free-plan library voices can return
`paid_plan_required`. Notes are not persistent, and browser autoplay or
microphone permissions can still block audio on some devices.
