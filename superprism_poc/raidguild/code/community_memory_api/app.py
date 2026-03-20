from __future__ import annotations

import hashlib
import logging
import secrets
import sys
import time
from datetime import timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response

from . import schemas
from .storage import Storage, StorageError

logger = logging.getLogger(__name__)


@dataclass
class Settings:
    base_dir: Path
    base: str = "superprism_poc"
    space: str = "raidguild"
    api_key: Optional[str] = None
    service_name: str = "prism-memory-api"
    root_path: str = ""
    strip_prefix: str = ""

    @property
    def data_root(self) -> Path:
        return self.base_dir / self.base / self.space


def create_app(settings: Settings) -> FastAPI:
    data_root = settings.data_root
    data_root.mkdir(parents=True, exist_ok=True)
    storage = Storage(data_root)

    code_path = settings.base_dir / settings.base / settings.space / "code"
    if str(code_path) not in sys.path:
        sys.path.append(str(code_path))
    try:
        from community_memory.config_loader import load_config as _load_config
        from community_knowledge.schemas import validate_metadata as _validate_metadata
    except ModuleNotFoundError as exc:
        raise RuntimeError("community_memory or community_knowledge package not found") from exc

    config_path = settings.base_dir / settings.base / settings.space / "config" / "space.json"
    knowledge_constraints = None
    allowed_kinds: list[str] = []
    try:
        space_config = _load_config(config_path)
        knowledge_constraints = space_config.knowledge.constraints
        allowed_kinds = space_config.knowledge.constraints.allowed_kinds
        if space_config.knowledge.kinds:
            allowed_kinds = sorted(set(allowed_kinds + space_config.knowledge.kinds))
    except FileNotFoundError:
        logger.warning("Knowledge config not found at %s; metadata validation disabled", config_path)

    app = FastAPI(title="Prism Memory API", version="0.1.0", root_path=settings.root_path or "")

    def _normalize_prefix(value: str) -> str:
        value = value.rstrip("/")
        if not value.startswith("/"):
            value = f"/{value}"
        return value

    prefixes_to_strip: list[str] = []
    if settings.strip_prefix:
        prefixes_to_strip.append(_normalize_prefix(settings.strip_prefix))
    if settings.root_path:
        prefixes_to_strip.append(_normalize_prefix(settings.root_path))
    prefixes_to_strip = [p for p in prefixes_to_strip if p and p != "/"]

    if prefixes_to_strip:
        @app.middleware("http")
        async def strip_prefix_middleware(request: Request, call_next):
            path = request.scope.get("path", "") or "/"
            for prefix in prefixes_to_strip:
                if path == prefix:
                    path = "/"
                elif path.startswith(prefix + "/"):
                    new_path = path[len(prefix):]
                    if not new_path.startswith("/"):
                        new_path = f"/{new_path}"
                    path = new_path or "/"
            request.scope["path"] = path or "/"
            return await call_next(request)

    logger.info(
        "Starting Prism Memory API (service=%s, root=%s, auth=%s, root_path=%s)",
        settings.service_name,
        data_root,
        "enabled" if settings.api_key else "disabled",
        settings.root_path or "/",
    )

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover
        logger.info("data_root=%s root_path=%s", data_root, settings.root_path or "/")

    def _error_response(code: str, message: str, status: int, headers: Optional[dict] = None) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={"error": {"code": code, "message": message}},
            headers=headers,
        )

    def require_api_key(
        prism_key: Optional[str] = Header(default=None, alias="X-Prism-Api-Key"),
        legacy_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ) -> None:
        api_key_value = prism_key or legacy_key
        if not settings.api_key:
            raise HTTPException(status_code=500, detail={"error": {"code": "api_key_not_configured", "message": "API key not configured"}})
        if not api_key_value:
            raise HTTPException(
                status_code=401,
                headers={"WWW-Authenticate": "API-Key"},
                detail={"error": {"code": "missing_api_key", "message": "X-Prism-Api-Key header required"}},
            )
        if not secrets.compare_digest(api_key_value, settings.api_key):
            logger.warning(
                "Invalid API key attempt sha256=%s",
                hashlib.sha256(api_key_value.encode()).hexdigest(),
            )
            raise HTTPException(
                status_code=401,
                headers={"WWW-Authenticate": "API-Key"},
                detail={"error": {"code": "invalid_api_key", "message": "Invalid API key"}},
            )

    @app.middleware("http")
    async def access_log_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.info("%s %s -> %s (%sms)", request.method, request.url.path, status, duration_ms)

    @app.exception_handler(StorageError)
    async def storage_error_handler(_: Request, exc: StorageError):  # type: ignore[override]
        mapping = {
            "invalid_date": 400,
            "invalid_bucket": 400,
            "invalid_slug": 400,
            "ambiguous_slug": 400,
            "invalid_query": 400,
            "not_found": 404,
            "malformed_json": 500,
        }
        status = mapping.get(exc.code, 500)
        return _error_response(exc.code, exc.message, status)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):  # type: ignore[override]
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=exc.headers)
        return _error_response("error", str(exc.detail), exc.status_code, headers=exc.headers)

    @app.get("/health", response_model=schemas.HealthResponse, tags=["system"])
    async def health() -> schemas.HealthResponse:
        return schemas.HealthResponse(service=settings.service_name, space=settings.space)

    auth_dependency = Depends(require_api_key)

    @app.get("/memory/latest", dependencies=[auth_dependency], tags=["memory"])
    async def memory_latest():
        return storage.memory_latest()

    @app.get("/latest", dependencies=[auth_dependency], tags=["memory"], include_in_schema=False)
    async def memory_latest_alias():
        return storage.memory_latest()

    @app.get("/memory/date/{date}", dependencies=[auth_dependency], tags=["memory"])
    async def memory_by_date(date: str):
        return storage.memory_by_date(date)

    @app.get("/date/{date}", dependencies=[auth_dependency], tags=["memory"], include_in_schema=False)
    async def memory_by_date_alias(date: str):
        return storage.memory_by_date(date)

    @app.get("/digests/date/{date}", dependencies=[auth_dependency], tags=["digests"])
    async def digests_by_date(date: str):
        return storage.digests_by_date(date)

    @app.get("/digests/bucket/{bucket}/date/{date}", dependencies=[auth_dependency], tags=["digests"])
    async def digest_for_bucket(bucket: str, date: str):
        return storage.digest_for_bucket(bucket, date)

    @app.get("/buckets/{bucket}/digests/{date}.{ext}", dependencies=[auth_dependency], tags=["digests"])
    async def bucket_digest_asset(bucket: str, date: str, ext: str):
        media_type, payload = storage.bucket_digest_asset(bucket, date, ext)
        if media_type == "text/markdown":
            return Response(content=payload, media_type=media_type)
        return payload

    @app.get("/activity/recent", dependencies=[auth_dependency], tags=["activity"])
    async def activity_recent(
        limit: int = Query(100, ge=1, le=1000),
        event_type: Optional[str] = Query(None, alias="type"),
        bucket: Optional[str] = None,
        collector_key: Optional[str] = None,
    ):
        return storage.activity_recent(limit=limit, event_type=event_type, bucket=bucket, collector_key=collector_key)

    @app.get("/products/suggestions/latest", dependencies=[auth_dependency], tags=["products"])
    async def product_suggestion_latest():
        return storage.product_suggestion_latest()

    @app.get("/products/suggestions/date/{date}", dependencies=[auth_dependency], tags=["products"])
    async def product_suggestion_by_date(date: str):
        return storage.product_suggestion_by_date(date)

    @app.get("/products/suggestions/weekly/{week}", dependencies=[auth_dependency], tags=["products"])
    async def product_suggestion_weekly(week: str):
        return storage.product_suggestion_weekly(week)

    @app.get("/knowledge/docs/{slug:path}", dependencies=[auth_dependency], tags=["knowledge"])
    async def knowledge_doc(slug: str):
        return storage.knowledge_doc(slug)

    @app.get("/knowledge/search", dependencies=[auth_dependency], tags=["knowledge"])
    async def knowledge_search(
        q: Optional[str] = Query(None, min_length=1),
        kind: Optional[str] = None,
        tag: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = Query(25, ge=1, le=100),
    ):
        return storage.knowledge_search(query=q, kind=kind, tag=tag, entity=entity, limit=limit)

    @app.get("/knowledge/indexes/manifest", dependencies=[auth_dependency], tags=["knowledge"])
    async def knowledge_index_manifest():
        return storage.knowledge_index("manifest")

    @app.get("/knowledge/indexes/tags", dependencies=[auth_dependency], tags=["knowledge"])
    async def knowledge_index_tags():
        return storage.knowledge_index("tags")

    @app.get("/knowledge/indexes/entities", dependencies=[auth_dependency], tags=["knowledge"])
    async def knowledge_index_entities():
        return storage.knowledge_index("entities")

    @app.post(
        "/knowledge/inbox",
        response_model=schemas.KnowledgeInboxResponse,
        dependencies=[auth_dependency],
        tags=["knowledge"],
    )
    async def knowledge_inbox(payload: schemas.KnowledgeInboxRequest):
        if not payload.content.strip():
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "empty_content", "message": "Content cannot be empty"}},
            )

        warnings: list[str] = []
        if knowledge_constraints is not None:
            result = _validate_metadata(
                payload.metadata,
                constraints=knowledge_constraints,
                allowed_kinds=allowed_kinds,
            )
            if not result.ok:
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "invalid_metadata", "message": "; ".join(result.errors[:10])}},
                )
            warnings = result.warnings

        try:
            entry = storage.write_knowledge_inbox_entry(
                payload.filename,
                payload.content,
                payload.metadata,
            )
        except StorageError as exc:
            return _error_response(exc.code, exc.message, 400 if exc.code != "not_found" else 404)

        response = schemas.KnowledgeInboxResponse(
            path=entry["doc_path"],
            metadata_path=entry["meta_path"],
            warnings=warnings or None,
        )
        return response

    @app.post(
        "/memory/inbox",
        response_model=schemas.MemoryInboxResponse,
        dependencies=[auth_dependency],
        tags=["memory"],
    )
    async def memory_inbox(entry: schemas.MemoryInboxRequest):
        source = entry.source.strip()
        msg_type = entry.type.strip()
        content = entry.content.strip()
        if not source or not msg_type or not content:
            raise HTTPException(
                status_code=400,
                detail={"error": {"code": "invalid_payload", "message": "source, type, and content are required"}},
            )
        ts_value = entry.ts
        if ts_value.tzinfo is None:
            ts_value = ts_value.replace(tzinfo=timezone.utc)
        ts_value = ts_value.astimezone(timezone.utc)
        ts_iso = ts_value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        payload = {
            "source": source,
            "type": msg_type,
            "content": content,
            "ts": ts_iso,
        }
        if entry.bucket:
            payload["bucket"] = entry.bucket
        if entry.bucket_hint:
            payload["bucket_hint"] = entry.bucket_hint
        if entry.author:
            payload["author"] = entry.author
        if entry.url:
            payload["url"] = entry.url
        path = storage.write_memory_inbox_entry(payload)
        return schemas.MemoryInboxResponse(path=path)

    return app
