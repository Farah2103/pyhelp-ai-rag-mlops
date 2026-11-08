import os
import threading
import time
import uuid
from pathlib import Path
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from src.common import ROOT, read_json
from src.generation.providers import ProviderError
from monitoring.events import record

class Ask(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if len(value) < 3 or "\x00" in value: raise ValueError("Invalid question")
        return value

@lru_cache(maxsize=1)
def get_assistant():
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    from src.embeddings.encoder import Encoder
    from src.retrieval.index import Retriever
    from src.generation.providers import LLM
    from src.generation.assistant import Assistant
    folder = Path(os.getenv("PYHELP_INDEX", str(ROOT / "artifacts/current")))
    cfg = read_json(folder / "manifest.json")["config"]
    return Assistant(Retriever(folder, Encoder(cfg["embedding_model"],cfg["embedding_revision"])), LLM())

app = FastAPI(title="PyHelp AI", version="0.1.0")
lock = threading.Lock()
@app.middleware("http")
async def observe(request: Request, call_next):
    request_id = str(uuid.uuid4()); start = time.perf_counter()
    request.state.status = "http_error"; request.state.chunks = 0
    response = await call_next(request)
    record({"request_id":request_id,"path":request.url.path,"http_status":response.status_code,
        "status":request.state.status if request.url.path == "/ask" else "health" if response.status_code==200 else "http_error",
        "latency_ms":(time.perf_counter()-start)*1000,"retrieved_chunks":request.state.chunks})
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/health")
def health():
    folder = Path(os.getenv("PYHELP_INDEX", str(ROOT / "artifacts/current")))
    ready = all((folder / x).is_file() for x in ["manifest.json","index.faiss","chunks.json"])
    # Liveness and artifact readiness only; this does not prove LLM availability.
    return {"status":"ok", "index_present":ready, "llm_checked":False,"documentation_version":"3.11.18"}

@app.post("/ask")
def ask(body: Ask, request: Request):
    try:
        with lock: result = get_assistant().ask(body.question)
        request.state.status = result["status"]; request.state.chunks = result["retrieved_chunks"]
        return result
    except ProviderError:
        request.state.status = "provider_error"
        raise HTTPException(503,"Generation provider unavailable") from None
    except Exception:
        request.state.status = "internal_error"
        raise HTTPException(503,"Assistant artifacts or dependencies unavailable") from None

@app.get("/", include_in_schema=False)
def ui(): return FileResponse(ROOT / "app/index.html")
