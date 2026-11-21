"""Unit tests for Obsidian-style in-place linked vaults and non-polluting caches."""

from pathlib import Path

import pytest

from core import linked_vaults


def test_link_and_unlink_keep_external_folder_untouched_and_unpolluted(tmp_path: Path) -> None:
    root = tmp_path / "realm_data"
    root.mkdir()
    vault = tmp_path / "external_docs" / "Yggdrasil HQ"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "Projects").mkdir()
    note = vault / "Projects" / "roadmap.md"
    note.write_text("# Roadmap\n\n## Q1\nLocal first.\n", encoding="utf-8")
    (vault / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")

    slug, resolved = linked_vaults.link_folder(vault, root)
    assert slug == "yggdrasil_hq"
    assert resolved == vault.resolve()
    assert linked_vaults.is_linked_vault(slug, root) is True
    assert linked_vaults.resolve_linked_path(slug, root) == vault.resolve()

    # Linking the exact same path again is idempotent
    slug2, _ = linked_vaults.link_folder(vault, root)
    assert slug2 == slug

    # Index and chat caches live in root/.vault_cache, NEVER inside the user's vault
    idx = linked_vaults.cache_index_for_dir(vault, root)
    chats = linked_vaults.linked_chats_path(slug, root)
    assert idx.parent == root.resolve() / ".vault_cache"
    assert chats.parent == root.resolve() / ".vault_cache"
    idx.write_text("[]", encoding="utf-8")
    chats.write_text("[]", encoding="utf-8")
    assert not (vault / "index.json").exists()
    assert not (vault / "chats.json").exists()
    assert not (vault / ".knowledge-area.json").exists()

    # Unlinking cleans only registry & local caches, never touching user files
    assert linked_vaults.unlink_folder(slug, root) is True
    assert linked_vaults.is_linked_vault(slug, root) is False
    assert not idx.exists()
    assert not chats.exists()
    assert note.is_file()
    assert (vault / ".obsidian" / "workspace.json").is_file()


def test_link_folder_rejects_symlinks_root_and_storage_dir(tmp_path: Path) -> None:
    root = tmp_path / "realm_data"
    root.mkdir()
    real_dir = tmp_path / "real_vault"
    real_dir.mkdir()
    sym = tmp_path / "sym_vault"
    sym.symlink_to(real_dir, target_is_directory=True)

    with pytest.raises(ValueError, match="symbolic links"):
        linked_vaults.link_folder(sym, root)
    with pytest.raises(ValueError, match="filesystem root"):
        linked_vaults.link_folder(root, root)
    with pytest.raises(ValueError, match="filesystem root"):
        linked_vaults.link_folder(Path("/"), root)


def test_duplicate_folder_names_get_unique_slugs(tmp_path: Path) -> None:
    root = tmp_path / "realm_data"
    root.mkdir()
    first = tmp_path / "a" / "Notes"
    second = tmp_path / "b" / "Notes"
    first.mkdir(parents=True)
    second.mkdir(parents=True)

    s1, _ = linked_vaults.link_folder(first, root)
    s2, _ = linked_vaults.link_folder(second, root)
    assert s1 == "notes"
    assert s2 == "notes_2"
