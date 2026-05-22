#!/usr/bin/env python3
"""FastAPI server exposing the AI Psychologist chatbot with SSE streaming."""
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

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

# In-memory session store: session_id -> chat_history list
sessions: dict[str, list] = {}
chain = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global chain
    vs = get_vectorstore()
    retriever = get_retriever(vs)
    chain = build_chain(retriever)
    yield


app = FastAPI(title="AI Psychologist", lifespan=lifespan)

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


@app.post("/session", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = str(uuid.uuid4())
    sessions[session_id] = []
    return SessionResponse(session_id=session_id)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    if chain is None:
        raise HTTPException(status_code=503, detail="Chain not ready")

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

            # Stream word by word for a natural feel
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


@app.delete("/session/{session_id}")
def clear_session(session_id: str) -> dict:
    sessions.pop(session_id, None)
    return {"cleared": True}


# Serve frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
