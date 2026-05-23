#!/usr/bin/env python3
"""FastAPI server exposing the AI Psychologist chatbot with SSE streaming."""
import asyncio
import json
import os
import shutil
import threading
import uuid
from pathlib import Path
from typing import AsyncIterator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from psychologist.chain import build_chain
from psychologist.vectorstore import get_retriever, get_vectorstore

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

sessions: dict[str, list] = {}
_chain = None
_chain_lock = threading.Lock()


def _ensure_chroma_writable() -> None:
    """Copy the bundled chroma_db to /tmp on Vercel (read-only deploy FS)."""
    if not os.getenv("VERCEL"):
        return
    src = Path(__file__).parent / "chroma_db"
    dst = Path("/tmp/chroma_db")
    if not dst.exists() and src.exists():
        shutil.copytree(str(src), str(dst))


def get_chain():
    global _chain
    if _chain is None:
        with _chain_lock:
            if _chain is None:
                _ensure_chroma_writable()
                vs = get_vectorstore()
                retriever = get_retriever(vs)
                _chain = build_chain(retriever)
    return _chain


app = FastAPI(title="AI Psychologist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class SessionResponse(BaseModel):
    session_id: str


class TTSRequest(BaseModel):
    text: str


@app.post("/session", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return SessionResponse(session_id=session_id)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    chain = get_chain()

    if req.session_id not in sessions:
        sessions[req.session_id] = []

    history = sessions[req.session_id]

    async def event_generator() -> AsyncIterator[str]:
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chain.invoke({"input": req.message, "chat_history": history}),
            )
            answer: str = result["answer"]

            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == 0 else " " + word
                payload = json.dumps({"token": chunk, "done": False})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.03)

            history.append(HumanMessage(content=req.message))
            history.append(AIMessage(content=answer))
            sessions[req.session_id] = history

            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/tts")
async def text_to_speech(req: TTSRequest) -> StreamingResponse:
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/audio/speech",
            headers={"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"},
            json={"model": "playai-tts", "input": req.text, "voice": "Celeste-PlayAI", "response_format": "mp3"},
        )

    if resp.status_code != 200:
        print(f"[Groq TTS] {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=502, detail=f"Groq TTS error {resp.status_code}")

    audio_bytes = resp.content
    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Length": str(len(audio_bytes))},
    )


@app.delete("/session/{session_id}")
def clear_session(session_id: str) -> dict:
    sessions.pop(session_id, None)
    return {"cleared": True}


# Serve frontend — public/ for Railway/local, Vercel CDN handles it there instead
_public_dir = Path(__file__).parent / "public"
if _public_dir.exists():
    app.mount("/", StaticFiles(directory=str(_public_dir), html=True), name="frontend")
