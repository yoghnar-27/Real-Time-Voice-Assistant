import asyncio
import contextlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from app.services.assistant import ask_gemini
from app.services.speech import create_deepgram_client, get_final_transcript

load_dotenv()

app = FastAPI()


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

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
            async def receive_deepgram_results():
                loop = asyncio.get_running_loop()

                def read_results():
                    try:
                        while not stop_receiver.is_set():
                            result = connection.recv()
                            transcript = get_final_transcript(result)
                            if transcript:
                                loop.call_soon_threadsafe(
                                    transcript_queue.put_nowait, transcript
                                )
                    except Exception as error:
                        loop.call_soon_threadsafe(
                            transcript_queue.put_nowait, error
                        )

                await asyncio.to_thread(read_results)

            receiver_task = asyncio.create_task(receive_deepgram_results())

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
                    await asyncio.to_thread(connection.send_media, completed.result())
                    continue

                transcript = completed.result()
                if isinstance(transcript, Exception):
                    raise RuntimeError(f"Deepgram error: {transcript}")

                await websocket.send_json({"type": "transcript", "text": transcript})
                response = await asyncio.to_thread(ask_gemini, transcript)
                await websocket.send_json({"type": "response", "text": response})

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