from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


_BUCKET_RE = re.compile(r"^[a-z0-9_-]+$")
_SAFE_DOC_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


class StorageError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Storage:
    """Filesystem-backed loader for Prism Memory artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.knowledge_root = (self.root / "knowledge" / "kb").resolve()
        self.knowledge_docs = (self.knowledge_root / "docs").resolve()
        self.knowledge_metadata = (self.knowledge_root / "metadata").resolve()
        self.knowledge_indexes = (self.knowledge_root / "indexes").resolve()
        self.knowledge_inbox = (self.knowledge_root / "triage" / "inbox").resolve()
        self.memory_inbox = (self.root / "inbox" / "memory" / "incoming").resolve()
        self._root_prefix = tuple(self.root.parts[-2:])

    def _load_json(self, path: Path) -> Any:
        if not path.is_file():
            raise StorageError("not_found", f"File not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except json.JSONDecodeError as exc:
            raise StorageError("malformed_json", f"Malformed JSON: {path.name}") from exc

    def memory_latest(self) -> Any:
        return self._load_json(self.root / "memory" / "rolling" / "latest.json")

    def memory_by_date(self, date_str: str) -> Any:
        self._validate_date(date_str)
        return self._load_json(self.root / "memory" / "rolling" / f"{date_str}.json")

    def digests_by_date(self, date_str: str) -> Dict[str, Any]:
        self._validate_date(date_str)
        buckets_dir = self.root / "buckets"
        result: Dict[str, Any] = {}
        if not buckets_dir.is_dir():
            raise StorageError("not_found", "No buckets directory present")
        for bucket_path in buckets_dir.iterdir():
            if not bucket_path.is_dir():
                continue
            digest_path = bucket_path / "digests" / f"{date_str}.json"
            if digest_path.is_file():
                result[bucket_path.name] = self._load_json(digest_path)
        if not result:
            raise StorageError("not_found", f"No digests found for {date_str}")
        return {"date": date_str, "buckets": result}

    def digest_for_bucket(self, bucket: str, date_str: str) -> Any:
        self._validate_date(date_str)
        self._validate_bucket(bucket)
        digest_path = self.root / "buckets" / bucket / "digests" / f"{date_str}.json"
        return self._load_json(digest_path)

    def bucket_digest_asset(self, bucket: str, date_str: str, extension: str) -> tuple[str, Any]:
        self._validate_date(date_str)
        self._validate_bucket(bucket)
        ext = extension.lower().lstrip(".")
        if ext not in {"json", "md"}:
            raise StorageError("invalid_format", "Digest format must be 'json' or 'md'")
        digest_path = self.root / "buckets" / bucket / "digests" / f"{date_str}.{ext}"
        if ext == "json":
            return ("application/json", self._load_json(digest_path))
        if not digest_path.is_file():
            raise StorageError("not_found", f"File not found: {digest_path}")
        try:
            content = digest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError("not_found", f"Unable to read digest: {digest_path}") from exc
        return ("text/markdown", content)

    def activity_recent(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        bucket: Optional[str] = None,
        collector_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        log_path = self.root / "activity" / "activity.jsonl"
        if not log_path.is_file():
            raise StorageError("not_found", "activity log missing")
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise StorageError("not_found", "Unable to read activity log") from exc
        entries: List[Dict[str, Any]] = []
        for raw in reversed(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                # skip malformed lines but keep processing
                continue
            if event_type and record.get("type") != event_type:
                continue
            if bucket and record.get("meta", {}).get("bucket") != bucket:
                continue
            if collector_key and record.get("meta", {}).get("collector_key") != collector_key:
                continue
            entries.append(record)
            if len(entries) >= limit:
                break
        return entries

    def knowledge_doc(self, slug: str) -> Dict[str, Any]:
        normalized, entry = self._resolve_manifest_entry(slug)
        doc_path = self._rooted_path(entry["path"])
        meta_path = self._rooted_path(entry["meta_path"])
        if not doc_path.is_file():
            raise StorageError("not_found", f"Knowledge doc missing at {doc_path}")
        metadata = self._load_json(meta_path)
        try:
            content = doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError("not_found", f"Unable to read document body: {doc_path}") from exc
        return {
            "slug": metadata.get("slug") or normalized,
            "path": str(doc_path.relative_to(self.root)),
            "meta_path": str(meta_path.relative_to(self.root)),
            "kind": metadata.get("kind"),
            "title": metadata.get("title"),
            "summary": metadata.get("summary"),
            "updated": metadata.get("updated"),
            "tags": metadata.get("tags"),
            "entities": metadata.get("entities"),
            "metadata": metadata,
            "content": content,
        }

    def knowledge_search(
        self,
        query: Optional[str] = None,
        kind: Optional[str] = None,
        tag: Optional[str] = None,
        entity: Optional[str] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        if not any([query, kind, tag, entity]):
            raise StorageError("invalid_query", "Provide at least one of q, kind, tag, or entity")
        normalized_query = (query or "").strip().lower()
        tokens = tuple(dict.fromkeys(token for token in normalized_query.split() if token))
        manifest = self._load_manifest()
        results: List[Dict[str, Any]] = []
        for entry in manifest:
            if kind and entry.get("kind") != kind:
                continue
            tags_list = entry.get("tags") or []
            entities_list = entry.get("entities") or []
            if tag and tag not in tags_list:
                continue
            if entity and entity not in entities_list:
                continue
            matched_tokens: Set[str] = set()
            match_sources: List[str] = []
            metadata_hits: Set[str] = set()
            body_hits: Set[str] = set()
            if tokens:
                haystack = " ".join(
                    [
                        entry.get("title", ""),
                        entry.get("summary", ""),
                        " ".join(tags_list),
                        " ".join(entities_list),
                    ]
                ).lower()
                metadata_hits = self._tokens_in_text(haystack, tokens)
                if metadata_hits:
                    matched_tokens.update(metadata_hits)
                    match_sources.append("metadata")
                if len(matched_tokens) < len(tokens):
                    body_hits = self._tokens_in_doc(entry, tokens)
                    if body_hits:
                        matched_tokens.update(body_hits)
                        match_sources.append("body")
                if not matched_tokens:
                    continue
                score = len(matched_tokens)
            else:
                score = 1
            slug_value = self._slug_from_entry(entry)
            results.append(
                {
                    "slug": slug_value,
                    "title": entry.get("title"),
                    "summary": entry.get("summary"),
                    "kind": entry.get("kind"),
                    "updated": entry.get("updated"),
                    "tags": tags_list,
                    "entities": entities_list,
                    "path": entry.get("path"),
                    "meta_path": entry.get("meta_path"),
                    "score": score,
                    "match_tokens": sorted(matched_tokens) if matched_tokens else [],
                    "match_sources": match_sources,
                }
            )
        results.sort(key=lambda item: (-item["score"], item.get("title") or ""))
        return {
            "query": query,
            "filters": {
                "kind": kind,
                "tag": tag,
                "entity": entity,
            },
            "total": len(results),
            "results": results[:limit],
        }

    def knowledge_index(self, name: str) -> Any:
        allowed = {"manifest", "tags", "entities"}
        if name not in allowed:
            raise StorageError("invalid_query", f"Unsupported knowledge index '{name}'")
        path = self.knowledge_indexes / f"{name}.json"
        return self._load_json(path)

    def product_suggestion_latest(self) -> Any:
        suggestions_dir = self.root / "products" / "suggestions"
        candidates = sorted(
            path
            for path in suggestions_dir.glob("????-??-??.json")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.json", path.name)
        )
        if not candidates:
            raise StorageError("not_found", "No daily product suggestions found")
        return self._load_json(candidates[-1])

    def product_suggestion_by_date(self, date_str: str) -> Any:
        self._validate_date(date_str)
        path = self.root / "products" / "suggestions" / f"{date_str}.json"
        return self._load_json(path)

    def product_suggestion_weekly(self, week_key: str) -> Any:
        self._validate_week(week_key)
        path = self.root / "products" / "suggestions" / f"weekly-{week_key}.json"
        return self._load_json(path)

    @staticmethod
    def _validate_date(date_str: str) -> None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
            raise StorageError("invalid_date", "Date must be YYYY-MM-DD")

    @staticmethod
    def _validate_bucket(bucket: str) -> None:
        if not _BUCKET_RE.fullmatch(bucket):
            raise StorageError("invalid_bucket", "Bucket may contain a-z, 0-9, '_' or '-' only")

    @staticmethod
    def _validate_week(week_key: str) -> None:
        if not re.fullmatch(r"\d{4}-W\d{2}", week_key):
            raise StorageError("invalid_date", "Week must be YYYY-WW")

    def write_knowledge_inbox_entry(
        self,
        filename: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, str]:
        normalized = Path(filename).name.strip()
        if not normalized:
            raise StorageError("invalid_filename", "Filename is required")
        stem, suffix = os.path.splitext(normalized)
        if not suffix:
            normalized = f"{normalized}.md"
        elif suffix.lower() != ".md":
            raise StorageError("invalid_filename", "Knowledge docs must use a .md extension")
        if not _SAFE_DOC_RE.fullmatch(normalized):
            raise StorageError("invalid_filename", "Filename may contain letters, numbers, '.', '_' or '-' only")

        inbox = self.knowledge_inbox
        inbox.mkdir(parents=True, exist_ok=True)
        doc_path = inbox / normalized
        if doc_path.exists():
            raise StorageError("file_exists", f"{doc_path.name} already exists")

        meta_path = doc_path.with_suffix(".meta.json")
        doc_path.write_text(content, encoding="utf-8")
        with meta_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")

        return {
            "doc_path": str(doc_path.relative_to(self.root)),
            "meta_path": str(meta_path.relative_to(self.root)),
        }

    def write_memory_inbox_entry(self, payload: Dict[str, Any]) -> str:
        required = ["source", "ts", "type", "content"]
        missing = [field for field in required if not str(payload.get(field, "")).strip()]
        if missing:
            raise StorageError("invalid_payload", f"Missing required inbox fields: {', '.join(missing)}")

        self.memory_inbox.mkdir(parents=True, exist_ok=True)
        source = str(payload["source"]).strip()
        slug = self._safe_slug(source)
        ts_value = str(payload["ts"]).strip()
        filename = f"{ts_value.replace(':', '').replace('-', '').replace('T', '_')}-{slug}-{uuid.uuid4().hex[:8]}.json"
        path = self.memory_inbox / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        return str(path.relative_to(self.root))

    @staticmethod
    def _safe_slug(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower()
        return slug or "inbox"

    def _resolve_manifest_entry(self, slug: str) -> Tuple[str, Dict[str, Any]]:
        normalized = self._normalize_slug(slug)
        manifest = self._load_manifest()
        matches: List[Tuple[Dict[str, Any], str]] = []
        for entry in manifest:
            rel_slug = self._relative_slug(entry)
            filename_slug = Path(rel_slug).name
            if normalized == rel_slug or normalized == filename_slug:
                matches.append((entry, rel_slug))
        if not matches:
            raise StorageError("not_found", f"No knowledge doc matched slug '{normalized}'")
        if len(matches) > 1:
            sample = matches[0][1]
            raise StorageError(
                "ambiguous_slug",
                f"Slug '{normalized}' matches multiple docs; try the full path like '{sample}'",
            )
        entry, rel_slug = matches[0]
        return rel_slug, entry

    def _normalize_slug(self, slug: str) -> str:
        cleaned = (slug or "").strip().strip("/")
        prefixes = [
            "knowledge/kb/docs/",
            "kb/docs/",
            "docs/",
        ]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]
                break
        if cleaned.endswith(".md"):
            cleaned = cleaned[: -len(".md")]
        if not cleaned:
            raise StorageError("invalid_slug", "Slug is required")
        parts = [part for part in cleaned.split("/") if part]
        for part in parts:
            if not _SAFE_DOC_RE.fullmatch(part):
                raise StorageError(
                    "invalid_slug",
                    "Slug components may contain letters, numbers, '.', '_' or '-' only",
                )
        return "/".join(parts)

    def _relative_slug(self, entry: Dict[str, Any]) -> str:
        path = self._rooted_path(entry["path"])
        try:
            relative = path.relative_to(self.knowledge_docs)
        except ValueError:
            relative = path
        return relative.with_suffix("").as_posix()

    def _slug_from_entry(self, entry: Dict[str, Any]) -> str:
        path = self._rooted_path(entry["path"])
        try:
            relative = path.relative_to(self.knowledge_docs)
            return relative.with_suffix("").as_posix()
        except ValueError:
            return path.stem

    def _tokens_in_text(self, text: str, tokens: Tuple[str, ...]) -> Set[str]:
        if not text:
            return set()
        haystack = text.lower()
        return {token for token in tokens if token and token in haystack}

    def _tokens_in_doc(self, entry: Dict[str, Any], tokens: Tuple[str, ...]) -> Set[str]:
        if not tokens:
            return set()
        doc_path = self._rooted_path(entry["path"])
        if not doc_path.is_file():
            return set()
        try:
            content = doc_path.read_text(encoding="utf-8").lower()
        except OSError:
            return set()
        return {token for token in tokens if token and token in content}

    def _rooted_path(self, raw_path: Any) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        if self._root_prefix:
            prefix_len = len(self._root_prefix)
            if len(path.parts) >= prefix_len and tuple(path.parts[:prefix_len]) == self._root_prefix:
                path = Path(*path.parts[prefix_len:])
        return (self.root / path).resolve()

    def _load_manifest(self) -> List[Dict[str, Any]]:
        manifest_path = self.knowledge_indexes / "manifest.json"
        return self._load_json(manifest_path)
