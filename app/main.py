import asyncio
import base64
import contextlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from deepgram.core.events import EventType
from app.services.assistant import ask_gemini
from app.services.speech import create_deepgram_client, get_final_transcript
from app.services.voice import text_to_speech

load_dotenv()

app = FastAPI()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Browser connected")

    connection = None
    receiver_task = None
    stop_receiver = asyncio.Event()
    transcript_queue = asyncio.Queue()
    try:
        deepgram = create_deepgram_client()

        # Deepgram SDK v7 exposes a synchronous WebSocket client. Keep its
        # blocking receive call in a worker thread so FastAPI stays responsive.
        with deepgram.listen.v1.connect(
            model="nova-3",
            language="en-US",
            smart_format=True,
            interim_results=True,
            endpointing=300,
        ) as connection:
            print("Deepgram connected")
            loop = asyncio.get_running_loop()

            def handle_deepgram_message(result):
                transcript = get_final_transcript(result)
                if transcript:
                    loop.call_soon_threadsafe(
                        transcript_queue.put_nowait, transcript
                    )

            def handle_deepgram_error(error):
                print("Deepgram error:", error)
                loop.call_soon_threadsafe(
                    transcript_queue.put_nowait,
                    RuntimeError(f"Deepgram error: {error}"),
                )

            def handle_deepgram_close(_message):
                if not stop_receiver.is_set():
                    error = RuntimeError("Deepgram connection closed")
                    print("Deepgram error:", error)
                    loop.call_soon_threadsafe(transcript_queue.put_nowait, error)

            connection.on(EventType.MESSAGE, handle_deepgram_message)
            connection.on(EventType.ERROR, handle_deepgram_error)
            connection.on(EventType.CLOSE, handle_deepgram_close)

            # start_listening() blocks while it receives Deepgram messages.
            # Run it in a worker so this coroutine can keep sending audio.
            receiver_task = asyncio.create_task(
                asyncio.to_thread(connection.start_listening)
            )

            while True:
                audio_task = asyncio.create_task(websocket.receive_bytes())
                transcript_task = asyncio.create_task(transcript_queue.get())
                done, pending = await asyncio.wait(
                    {audio_task, transcript_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

                completed = done.pop()
                if completed is audio_task:
                    audio = completed.result()
                    print("Audio received")
                    await asyncio.to_thread(connection.send_media, audio)
                    continue

                transcript = completed.result()
                if isinstance(transcript, Exception):
                    raise transcript

                print("Transcript:", transcript)
                await websocket.send_json({"type": "transcript", "text": transcript})
                try:
                    response = await asyncio.to_thread(ask_gemini, transcript)
                except Exception as error:
                    print("Gemini error:", error)
                    await websocket.send_json({
                        "type": "error",
                        "text": f"Gemini error: {error}",
                    })
                    continue

                print("Gemini response:", response)
                await websocket.send_json({"type": "response", "text": response})

                try:
                    print("Generating voice")
                    audio = await asyncio.to_thread(text_to_speech, response)
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64.b64encode(audio).decode("ascii"),
                    })
                except Exception as error:
                    print("ElevenLabs error:", error)
                    await websocket.send_json({
                        "type": "error",
                        "text": f"ElevenLabs error: {error}",
                    })

    except WebSocketDisconnect:
        print("Browser disconnected")
    except Exception as error:
        print("Voice assistant error:", error)
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "error", "text": str(error)})

    finally:
        stop_receiver.set()
        if connection is not None:
            with contextlib.suppress(Exception):
                await asyncio.to_thread(connection.send_close_stream)
        if receiver_task is not None:
            receiver_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await receiver_task