from __future__ import annotations

import argparse
import json
import os
import time
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse, unquote
from threading import RLock

StoreEntry = Dict[str, Any]  # { "value": ..., "created_at": float, "ttl_seconds": Optional[int] }


def now_ts() -> float:
    return time.time()


def is_expired(entry: StoreEntry, at: Optional[float] = None) -> bool:
    ttl = entry.get("ttl_seconds")
    if ttl is None:
        return False
    if not isinstance(ttl, int) or ttl < 0:
        # treat invalid TTL as "no TTL"
        return False
    at = now_ts() if at is None else at
    created_at = entry.get("created_at")
    if not isinstance(created_at, (int, float)):
        return False
    return (created_at + ttl) <= at


def atomic_write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="kv_", suffix=".tmp", dir=os.path.dirname(os.path.abspath(path)) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass


class KVStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = RLock()
        self._data: Dict[str, StoreEntry] = {}
        self.load()

    def load(self) -> None:
        with self._lock:
            if not os.path.exists(self.db_path):
                self._data = {}
                return
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self._data = raw  # type: ignore[assignment]
                else:
                    self._data = {}
            except (OSError, json.JSONDecodeError):
                self._data = {}

            self._prune_expired_locked()
            self._save_locked()

    def _save_locked(self) -> None:
        atomic_write_json(self.db_path, self._data)

    def _prune_expired_locked(self) -> None:
        ts = now_ts()
        expired_keys = [k for k, v in self._data.items() if isinstance(v, dict) and is_expired(v, ts)]
        for k in expired_keys:
            self._data.pop(k, None)

    def list_keys(self) -> Dict[str, Any]:
        with self._lock:
            self._prune_expired_locked()
            self._save_locked()
            return {"count": len(self._data), "keys": sorted(self._data.keys())}

    def get(self, key: str) -> Optional[StoreEntry]:
        with self._lock:
            self._prune_expired_locked()
            entry = self._data.get(key)
            if entry is None:
                self._save_locked()
                return None
            if not isinstance(entry, dict):
                return None
            self._save_locked()
            return entry

    def create(self, key: str, value: Any, ttl_seconds: Optional[int]) -> bool:
        with self._lock:
            self._prune_expired_locked()
            if key in self._data:
                self._save_locked()
                return False
            entry: StoreEntry = {"value": value, "created_at": now_ts(), "ttl_seconds": ttl_seconds}
            self._data[key] = entry
            self._save_locked()
            return True

    def upsert(self, key: str, value: Any, ttl_seconds: Optional[int]) -> StoreEntry:
        with self._lock:
            self._prune_expired_locked()
            entry: StoreEntry = {"value": value, "created_at": now_ts(), "ttl_seconds": ttl_seconds}
            self._data[key] = entry
            self._save_locked()
            return entry

    def delete(self, key: str) -> bool:
        with self._lock:
            self._prune_expired_locked()
            existed = key in self._data
            self._data.pop(key, None)
            self._save_locked()
            return existed


class Handler(BaseHTTPRequestHandler):
    server_version = "KVAPI/0.1"

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Any:
        length = self.headers.get("Content-Length")
        if not length:
            return None
        try:
            n = int(length)
        except ValueError:
            raise ValueError("Invalid Content-Length")
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON")

    def _require_auth(self) -> bool:
        api_key = self.server.api_key  # type: ignore[attr-defined]
        if not api_key:
            return True
        got = self.headers.get("X-API-Key")
        if got != api_key:
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized", "hint": "Provide X-API-Key header"})
            return False
        return True

    def _route(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"
        return path

    def do_GET(self) -> None:
        if not self._require_auth():
            return
        path = self._route()

        if path == "/health":
            return self._json(HTTPStatus.OK, {"status": "ok"})

        if path == "/items":
            return self._json(HTTPStatus.OK, self.server.store.list_keys())  # type: ignore[attr-defined]

        if path.startswith("/items/"):
            key = unquote(path[len("/items/"):])
            if not key:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "Missing key"})
            entry = self.server.store.get(key)  # type: ignore[attr-defined]
            if entry is None:
                return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found", "key": key})
            return self._json(HTTPStatus.OK, {"key": key, **entry})

        return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self._require_auth():
            return
        path = self._route()
        if path != "/items":
            return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        try:
            body = self._read_json()
        except ValueError as e:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})

        if not isinstance(body, dict):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be an object"})

        key = body.get("key")
        if not isinstance(key, str) or not key.strip():
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Field 'key' must be a non-empty string"})

        value = body.get("value")
        ttl = body.get("ttl_seconds")
        if ttl is not None and (not isinstance(ttl, int) or ttl < 0):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Field 'ttl_seconds' must be an int >= 0 or null"})

        created = self.server.store.create(key, value, ttl)  # type: ignore[attr-defined]
        if not created:
            return self._json(HTTPStatus.CONFLICT, {"error": "Key already exists", "key": key})

        return self._json(HTTPStatus.CREATED, {"ok": True, "key": key})

    def do_PUT(self) -> None:
        if not self._require_auth():
            return
        path = self._route()
        if not path.startswith("/items/"):
            return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        key = unquote(path[len("/items/"):])
        if not key:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Missing key"})

        try:
            body = self._read_json()
        except ValueError as e:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": str(e)})

        if not isinstance(body, dict):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be an object"})

        if "value" not in body:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Field 'value' is required"})

        value = body.get("value")
        ttl = body.get("ttl_seconds")
        if ttl is not None and (not isinstance(ttl, int) or ttl < 0):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Field 'ttl_seconds' must be an int >= 0 or null"})

        entry = self.server.store.upsert(key, value, ttl)  # type: ignore[attr-defined]
        return self._json(HTTPStatus.OK, {"ok": True, "key": key, **entry})

    def do_DELETE(self) -> None:
        if not self._require_auth():
            return
        path = self._route()
        if not path.startswith("/items/"):
            return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        key = unquote(path[len("/items/"):])
        if not key:
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Missing key"})

        existed = self.server.store.delete(key)  # type: ignore[attr-defined]
        if not existed:
            return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found", "key": key})
        return self._json(HTTPStatus.OK, {"ok": True, "deleted": key})

    def log_message(self, fmt: str, *args) -> None:
        # quieter logs; comment out if you want the default noisy logs
        print(f"[{self.log_date_time_string()}] {self.command} {self.path} -> {fmt % args}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default="kv_db.json", help="Path to JSON file for persistence")
    parser.add_argument("--api-key", default="", help="If set, require X-API-Key header")
    args = parser.parse_args()

    store = KVStore(args.db)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.store = store  # type: ignore[attr-defined]
    httpd.api_key = args.api_key  # type: ignore[attr-defined]

    print(f"KV API running on http://{args.host}:{args.port}")
    print(f"DB file: {os.path.abspath(args.db)}")
    if args.api_key:
        print("Auth enabled: send header X-API-Key")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
