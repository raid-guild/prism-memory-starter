from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import uvicorn

from .app import Settings, create_app

logger = logging.getLogger(__name__)


def infer_root_path(explicit: str, fallback_url: str | None) -> str:
    if explicit:
        return explicit
    if not fallback_url:
        return ""
    parsed = urlparse(fallback_url)
    path = parsed.path or ""
    # Normalize so "/" becomes "" while nested paths keep their leading slash.
    if path in ("", "/"):
        return ""
    return path.rstrip("/")


def infer_strip_prefix(explicit: str, agent_id: str | None) -> str:
    if explicit:
        return explicit.rstrip("/")
    if agent_id:
        return f"/agents/{agent_id}".rstrip("/")
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prism Memory API server")
    parser.add_argument("--host", default=os.getenv("OPENCLAW_MEMORY_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("OPENCLAW_MEMORY_API_PORT", "8788")))
    parser.add_argument("--base", default=os.getenv("OPENCLAW_MEMORY_API_BASE", "superprism_poc"))
    parser.add_argument("--space", default=os.getenv("OPENCLAW_MEMORY_API_SPACE", "raidguild"))
    parser.add_argument("--api-key", default=os.getenv("OPENCLAW_MEMORY_API_KEY"))
    parser.add_argument("--root-path", default=os.getenv("OPENCLAW_MEMORY_API_ROOT_PATH", ""))
    parser.add_argument(
        "--memory-api-url",
        default=os.getenv("MEMORY_API_URL"),
        help="Full external URL (used to infer root_path when --root-path is omitted)",
    )
    parser.add_argument(
        "--strip-prefix",
        default=os.getenv("OPENCLAW_MEMORY_API_STRIP_PREFIX", ""),
        help="Optional path prefix (e.g. /agents/xbp1hytd) to strip before FastAPI routing",
    )
    parser.add_argument("--log-level", default=os.getenv("OPENCLAW_MEMORY_API_LOG_LEVEL", "info"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("OPENCLAW_MEMORY_API_KEY (or --api-key) must be set")

    root_path = infer_root_path(args.root_path, args.memory_api_url)
    strip_prefix = infer_strip_prefix(args.strip_prefix, os.getenv("AGENT_ID"))

    base_dir = Path(__file__).resolve().parents[4]
    settings = Settings(
        base_dir=base_dir,
        base=args.base,
        space=args.space,
        api_key=args.api_key,
        root_path=root_path,
        strip_prefix=strip_prefix,
    )
    app = create_app(settings)

    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
