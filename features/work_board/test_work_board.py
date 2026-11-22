"""Unit and router tests for Projects, Kanban Board, Task Manager, and Local Calendar (.ics)."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.work_board import extractor, ics_codec, router, service, store


def _make_client(tmp_path: Path, *, local_only: bool = True) -> TestClient:
    cfg = WorkspaceConfig(app_title="Work Test", knowledge_dir="demo_ws", active_dirs=["demo_ws"], strict_local_only=local_only)
    (tmp_path / "demo_ws").mkdir(parents=True, exist_ok=True)

    def _resolve(chat_id: str, turn_index: int | None, doc_id: str, text: str) -> str:
        return text or f"Resolved {chat_id}:{turn_index}:{doc_id}"

    def _sync(area: str, filename: str, content: str) -> dict[str, object]:
        out = tmp_path / area / filename
        out.write_text(content, encoding="utf-8")
        return {"ok": True, "doc_id": filename.removesuffix(".md"), "bytes": len(content)}

    app = FastAPI()
    app.include_router(router.build_router(lambda: cfg, _resolve, None, _sync, lambda: tmp_path))
    return TestClient(app)


def test_store_roundtrip_and_corrupt_recovery(tmp_path: Path) -> None:
    path = tmp_path / "work_board.json"
    state = store.load_board(path)
    assert [c.id for c in state.columns] == ["todo", "doing", "review", "done"]
    state, proj = service.add_project(state, "Launch Q2", "Ship desktop OS", "#38D399", "active", "2026-06-30", 40.0)
    state, task = service.add_task(state, "Draft slides", "todo", proj.id, priority="high", due_date="2026-05-01")
    store.save_board(state, path)
    reloaded = store.load_board(path)
    assert reloaded.projects[0].title == "Launch Q2"
    assert reloaded.tasks[0].id == task.id
    path.write_text("{corrupt-json", encoding="utf-8")
    recovered = store.load_board(path)
    assert len(recovered.columns) == 4
    assert list(tmp_path.glob("work_board.json.corrupt*"))


def test_recurring_completion_and_month_end_clamping() -> None:
    assert store.advance_due_date("2024-01-31", "monthly") == "2024-02-29"
    assert store.advance_due_date("2025-01-31", "monthly") == "2025-02-28"
    assert store.advance_due_date("2026-05-01", "weekly") == "2026-05-08"
    state = store.WorkBoardState(columns=store.default_columns())
    state, task = service.add_task(state, "Weekly review", "todo", due_date="2026-05-01", recurrence="weekly")
    state, moved = service.reorder_task(state, task.id, "done", 0)
    assert moved is not None and moved.completed_at != ""
    open_tasks = [t for t in state.tasks if t.column_id != "done"]
    assert len(open_tasks) == 1
    assert open_tasks[0].due_date == "2026-05-08"
    assert open_tasks[0].title == "Weekly review"


def test_ics_export_import_roundtrip_and_dedup() -> None:
    state = store.WorkBoardState(columns=store.default_columns())
    state, _ = service.add_event(state, "Client Review, Q2; Final", "2026-05-14", "10:00", "11:30", "milestone", "Line 1\nLine 2")
    state, _ = service.add_task(state, "Deliver report", "todo", due_date="2026-05-20")
    ics_text = ics_codec.export_ics(state, "My Work")
    assert "BEGIN:VCALENDAR" in ics_text
    assert "SUMMARY:Client Review\\, Q2\\; Final" in ics_text
    assert "SUMMARY:[Task] Deliver report" in ics_text
    imported = ics_codec.import_ics(ics_text)
    assert len(imported) == 2
    assert imported[0].title == "Client Review, Q2; Final"
    assert imported[0].start_time == "10:00" and imported[0].end_time == "11:30"
    assert imported[0].notes == "Line 1\nLine 2"
    deduped = ics_codec.import_ics(ics_text, {ev.uid for ev in imported})
    assert deduped == []


def test_deterministic_and_ai_task_extraction() -> None:
    raw = "- [ ] Urgent: Finalize budget by 2026-06-01\n- [x] Already done\n2. Prepare client slides\nTODO: Follow up with design team"
    tasks = extractor.extract_tasks_deterministic(raw)
    assert len(tasks) == 3
    assert tasks[0]["priority"] == "urgent" and tasks[0]["due_date"] == "2026-06-01"

    async def _fake_stream(_msgs: list[dict[str, str]], _cfg: object, **_kw: object) -> AsyncIterator[dict[str, object]]:
        yield {"type": "token", "delta": '<tasks_json>[{"title":"Audit KPIs","description":"Q2 metrics","priority":"high","due_date":"2026-06-15"}]</tasks_json>'}

    ai_tasks, mode = asyncio.run(extractor.extract_tasks_with_ai("Review metrics", _fake_stream, object()))  # type: ignore[arg-type]
    assert mode == "ai" and len(ai_tasks) == 1 and ai_tasks[0]["title"] == "Audit KPIs"


def test_work_board_router_end_to_end(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    r0 = client.get("/api/work-board")
    assert r0.status_code == 200 and len(r0.json()["columns"]) == 4

    p = client.post("/api/work-board/projects", json={"title": "Impact Report", "color": "#38D399"}).json()["item"]
    t1 = client.post("/api/work-board/tasks", json={"title": "Collect interviews", "project_id": p["id"], "priority": "high", "due_date": "2026-05-10"}).json()["item"]
    t2 = client.post("/api/work-board/tasks", json={"title": "Build slides", "project_id": p["id"], "due_date": "2026-05-12"}).json()["item"]
    moved = client.post("/api/work-board/tasks/reorder", json={"task_id": t2["id"], "target_column_id": "doing", "target_index": 0})
    assert moved.status_code == 200 and moved.json()["item"]["column_id"] == "doing"

    ext = client.post("/api/work-board/extract", json={"text": "- [ ] Verify figures\n- [ ] Send PDF", "project_id": p["id"]})
    assert ext.status_code == 200 and ext.json()["created_count"] == 2

    ev = client.post("/api/work-board/events", json={"title": "Deep Focus Block", "date": "2026-05-11", "start_time": "09:00", "end_time": "11:00", "kind": "focus"})
    assert ev.status_code == 200

    ics_dl = client.get("/api/work-board/calendar.ics")
    assert ics_dl.status_code == 200 and "text/calendar" in ics_dl.headers["content-type"]
    imp = client.post("/api/work-board/calendar/import-ics", json={"ics_text": "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:ext-1\r\nSUMMARY:Workshop\r\nDTSTART:20260518T140000\r\nDTEND:20260518T153000\r\nEND:VEVENT\r\nEND:VCALENDAR"})
    assert imp.status_code == 200 and imp.json()["imported_count"] == 1

    sync = client.post("/api/work-board/sync-vault")
    assert sync.status_code == 200 and (tmp_path / "demo_ws" / "work_board_snapshot.md").is_file()
    md = (tmp_path / "demo_ws" / "work_board_snapshot.md").read_text(encoding="utf-8")
    assert "Impact Report" in md and "Collect interviews" in md and "Deep Focus Block" in md

    assert client.delete(f"/api/work-board/tasks/{t1['id']}").status_code == 200
    assert client.delete(f"/api/work-board/projects/{p['id']}").status_code == 200
    assert client.post("/api/work-board/events", json={"title": "Bad Date", "date": "2026-99-99"}).status_code == 400
    assert client.post("/api/work-board/tasks", json={"title": "Wrong WS"}, headers={"x-knowledge-area": "other_ws"}).status_code == 409
