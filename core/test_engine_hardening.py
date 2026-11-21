"""Regression tests for P2/P4 engine durability, Ollama OOM coordination, and cross-platform packaging."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from core import db, desktop_support, linked_vaults, model_routing, runtime
from core.contracts import KnowledgeChunk

ROOT = Path(__file__).resolve().parent.parent


def test_ollama_slot_serializes_calls_and_unloads_on_switch_and_cloud(monkeypatch: pytest.MonkeyPatch) -> None:
    unloaded: list[str] = []
    monkeypatch.setattr(model_routing, "_post_unload", unloaded.append)
    monkeypatch.setattr(model_routing, "_LAST_OLLAMA_MODEL", "")
    overlap = 0
    active = 0
    lock = threading.Lock()

    def worker(model: str) -> None:
        nonlocal active, overlap
        with model_routing.ollama_slot("ollama", model):
            with lock:
                active += 1
                overlap = max(overlap, active)
            time.sleep(0.05)
            with lock:
                active -= 1

    t1 = threading.Thread(target=worker, args=("",))
    t2 = threading.Thread(target=worker, args=("llama3.2:3b",))
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    assert overlap == 1
    assert model_routing.DEFAULT_LOCAL_MODEL in unloaded or "llama3.2:3b" in unloaded
    with model_routing.ollama_slot("openai", "gpt-4o-mini"):
        pass
    assert len(unloaded) >= 2


def test_db_schema_version_embedding_meta_and_corrupt_backups(tmp_path: Path) -> None:
    idx = tmp_path / "index.json"
    chunk = KnowledgeChunk(
        id="c1",
        doc_id="doc1",
        title="Doc",
        content="Hello",
        tags=[],
        file_path="doc1.md",
        embedding=[0.1, 0.2, 0.3],
    )
    db.save_chunks([chunk], idx, embedding_model="nomic-embed-text:v1.5", embedding_provider="ollama")
    loaded, meta = db.load_chunks_meta(idx)
    assert len(loaded) == 1
    assert meta["schema_version"] == db.CHUNK_SCHEMA_VERSION
    assert meta["embedding_provider"] == "ollama"
    assert meta["embedding_model"] == "nomic-embed-text:v1.5"
    assert meta["embedding_dim"] == 3
    idx.write_text("{bad-1", encoding="utf-8")
    assert db.load_chunks(idx) == []
    assert (tmp_path / "index.json.corrupt").is_file()
    idx.write_text("{bad-2", encoding="utf-8")
    assert db.load_chunks(idx) == []
    assert any(p.name.startswith("index.json.corrupt.") for p in tmp_path.iterdir())


def test_validate_external_folder_blocks_system_hidden_and_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "data"
    root.mkdir()
    hidden = tmp_path / ".secret"
    hidden.mkdir()
    with pytest.raises(ValueError, match="hidden"):
        linked_vaults.validate_external_folder(hidden, root)
    real_ext = tmp_path / "vault_ext"
    real_ext.mkdir()
    sym = tmp_path / "sym_vault"
    sym.symlink_to(real_ext)
    with pytest.raises(ValueError, match="symbolic links"):
        linked_vaults.validate_external_folder(sym, root)
    with pytest.raises(ValueError, match="internal storage"):
        linked_vaults.validate_external_folder(root, root)
    assert linked_vaults.validate_external_folder(real_ext, root) == real_ext.resolve()


def test_runtime_site_packages_data_root_and_desktop_active_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REALM_DATA_DIR", raising=False)
    monkeypatch.setattr(runtime, "is_frozen", lambda: False)
    monkeypatch.setattr(runtime, "_is_installed_package", lambda: True)
    monkeypatch.setattr(runtime, "desktop_data_dir", lambda: tmp_path / "user_data")
    assert runtime.data_root() == tmp_path / "user_data"
    desktop_support.record_active_url(tmp_path, "http://127.0.0.1:41234")
    active_file = tmp_path / desktop_support.ACTIVE_URL_FILE
    assert active_file.read_text(encoding="utf-8").strip() == "http://127.0.0.1:41234"
    desktop_support.clear_active_url(tmp_path)
    assert not active_file.exists()


def test_packaging_hygiene_dockerignore_and_macos_spec_exclude_dlls() -> None:
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert "!examples/starter_vault/**" in dockerignore
    assert "!core/**" in dockerignore
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "HOME=/data" in dockerfile and "REALM_ALLOW_NON_LOOPBACK=1" in dockerfile
    spec = (ROOT / "packaging" / "realm-engine.spec").read_text(encoding="utf-8")
    assert 'collect_data_files("webview", subdir="js")' in spec
    assert "VSVersionInfo" in spec
    build_sh = (ROOT / "packaging" / "build_macos.sh").read_text(encoding="utf-8")
    assert "-perm +111" in build_sh and "*.dll" in build_sh and "*.jar" in build_sh
