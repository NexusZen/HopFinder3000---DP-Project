import asyncio
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
import logging
import os
import time
import uuid

from fastapi import FastAPI, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .errors import InspectorError
from .probe_service import ProbeService
from .model_service import ModelService
from .inspector_service import InspectorService
from .document_service import extract_document, MAX_UPLOAD_BYTES, MAX_CONTEXT_CHARS
from .report_service import make_report

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT.parent / ".model-cache"))


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=1500)
    context: str = Field(min_length=1, max_length=MAX_CONTEXT_CHARS)
    inject_test_error: bool = False
    source_name: str | None = Field(default=None, max_length=240)

    @field_validator("question", "context")
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Provide nonempty readable text.")
        return value.strip()


class ScoreRequest(AnalyzeRequest):
    hops: list[str] = Field(min_length=1, max_length=30)

    @field_validator("hops")
    @classmethod
    def clean_hops(cls, value):
        if any(not h.strip() or len(h) > 4000 for h in value):
            raise ValueError("Hops must be nonempty statements up to 4,000 characters each.")
        return [h.strip() for h in value]


def load_service():
    path = Path(os.environ.get("PROBE_PATH", ROOT / "models" / "hop_error_probe.joblib"))
    probe = ProbeService(path)
    return InspectorService(ModelService(probe), probe)


def create_app(service_factory=load_service):
    state = dict(status="loading", message="Loading the trained probe and matching Qwen checkpoint. The first run may download model weights.")
    service = None
    inference_lock, reports_lock = Lock(), Lock()
    reports = OrderedDict()

    @asynccontextmanager
    async def lifespan(app):
        async def initialize():
            nonlocal service
            try:
                service = await asyncio.to_thread(service_factory)
                state.update(status="ready", model_name=service.probe.model_name, layer=service.probe.layer,
                             threshold=service.probe.threshold, device=service.model.device,
                             message=" ".join(service.model.warnings))
            except Exception as exc:
                logging.exception("Model initialization failed")
                state.update(status="error", message=str(exc))
        task = asyncio.create_task(initialize())
        yield
        if not task.done():
            task.cancel()

    app = FastAPI(title="Reasoning Error Inspector", lifespan=lifespan)

    @app.exception_handler(InspectorError)
    async def inspector_error(request, exc):
        return JSONResponse(status_code=exc.status, content={"detail": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        messages = [f"{'.'.join(str(x) for x in error['loc'][1:])}: {error['msg']}" for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": {"code": "invalid_input", "message": "; ".join(messages)}})

    def available():
        if state["status"] != "ready" or service is None:
            raise InspectorError(state["message"], "model_not_ready", 503)
        return service

    @app.get("/api/health")
    def health():
        return state.copy()

    @app.post("/api/analyze")
    def analyze(data: AnalyzeRequest):
        current = available()
        if not inference_lock.acquire(blocking=False):
            raise InspectorError("Another analysis is running. Try again when it finishes.", "busy", 409)
        try:
            result = current.analyze_request(data.question, data.context, data.inject_test_error, data.source_name)
            report_id = str(uuid.uuid4())
            result["report_id"] = report_id
            with reports_lock:
                reports[report_id] = (time.monotonic(), result)
                while len(reports) > 32:
                    reports.popitem(last=False)
            return result
        except InspectorError:
            raise
        except Exception as exc:
            logging.exception("Inference failed")
            raise InspectorError("Analysis could not finish. Check the server log and available memory, then try a shorter input.", "inference_failed", 500) from exc
        finally:
            inference_lock.release()

    @app.post("/api/score")
    def score(data: ScoreRequest):
        """Manual-hop verification endpoint. No generation or injection occurs here."""
        if data.inject_test_error:
            raise InspectorError("Use /api/analyze for controlled injection.")
        current = available()
        if not inference_lock.acquire(blocking=False):
            raise InspectorError("Another analysis is running.", "busy", 409)
        try:
            return current.probe.analyze_hops_with_probe(current.model, data.question, data.context, data.hops)
        finally:
            inference_lock.release()

    @app.post("/api/documents")
    async def document(file: UploadFile = File(...)):
        try:
            content = await file.read(MAX_UPLOAD_BYTES+1)
            text = await asyncio.to_thread(extract_document, file.filename, content)
            name = (file.filename or "Document").replace("\\", "/").split("/")[-1][:240]
            return dict(name=name, text=text, characters=len(text))
        finally:
            await file.close()

    @app.get("/api/reports/{report_id}.pdf")
    def report(report_id: uuid.UUID):
        with reports_lock:
            saved = reports.get(str(report_id))
            if not saved or time.monotonic()-saved[0] > 3600:
                raise InspectorError("This in-memory report expired. Run the analysis again.", "report_expired", 404)
            result = saved[1]
        return Response(make_report(result), media_type="application/pdf",
                        headers={"Content-Disposition": 'attachment; filename="reasoning-diagnostic.pdf"'})

    dist = ROOT.parent / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
