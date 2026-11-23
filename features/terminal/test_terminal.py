"""Unit & integration tests for the local-only integrated Terminal slice."""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from features.terminal import router as terminal_router
from features.terminal import service


def test_terminal_lifecycle_exec_stream_signal_and_cleanup(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(terminal_router.build_router(lambda: tmp_path))
    client = TestClient(app)
    try:
        res = client.post("/api/terminal/sessions", json={"label": "Dev Shell", "cols": 100, "rows": 24})
        assert res.status_code == 200
        sess = res.json()["session"]
        sid = sess["id"]
        assert sess["label"] == "Dev Shell" and sess["cwd"] == str(tmp_path) and sess["running"] is True
        assert any(s["id"] == sid for s in client.get("/api/terminal/sessions").json()["sessions"])

        assert client.post(f"/api/terminal/sessions/{sid}/resize", json={"cols": 120, "rows": 32}).status_code == 200
        assert client.post(f"/api/terminal/sessions/{sid}/input", json={"data": "echo REALM_TERM_PROBE_42\n"}).status_code == 200
        assert client.post(f"/api/terminal/sessions/{sid}/input", json={"data": "exit\n"}).status_code == 200

        collected = ""
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and "REALM_TERM_PROBE_42" not in collected:
            entry = service.get_session_entry(sid)
            assert entry is not None
            collected = "".join(txt for _, txt in list(entry["history"]))
            time.sleep(0.05)
        assert "REALM_TERM_PROBE_42" in collected

        # Stream endpoint replays scrollback cleanly and emits exit once shell ends
        with client.stream("GET", f"/api/terminal/sessions/{sid}/stream") as stream:
            assert stream.status_code == 200
            raw_sse = "".join(stream.iter_text())
        assert "REALM_TERM_PROBE_42" in raw_sse and "event: exit" in raw_sse

        assert client.delete(f"/api/terminal/sessions/{sid}").status_code == 200
        assert client.delete(f"/api/terminal/sessions/{sid}").status_code == 404
        assert client.post(f"/api/terminal/sessions/{sid}/input", json={"data": "hi\n"}).status_code == 404
    finally:
        service.close_all_sessions()


def test_terminal_session_cap_and_signal_validation(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(terminal_router.build_router(lambda: tmp_path))
    client = TestClient(app)
    try:
        created = []
        for idx in range(service.MAX_SESSIONS):
            r = client.post("/api/terminal/sessions", json={"label": f"S{idx}"})
            assert r.status_code == 200
            created.append(r.json()["session"]["id"])
        assert client.post("/api/terminal/sessions", json={"label": "Overflow"}).status_code == 429
        assert client.post(f"/api/terminal/sessions/{created[0]}/signal", json={"signal": "interrupt"}).status_code == 200
        # Verify JSON error hygiene on invalid signal
        bad = client.post(f"/api/terminal/sessions/{created[0]}/signal", json={"signal": "kill9"})
        assert bad.status_code == 422 and json.loads(bad.text)
    finally:
        service.close_all_sessions()
