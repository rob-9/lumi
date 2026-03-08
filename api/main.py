"""Lumi API — FastAPI backend for the chat-first UI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chat, sublabs

app = FastAPI(title="Lumi API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(sublabs.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
