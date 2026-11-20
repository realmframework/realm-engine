"""Keep usage ledger tests and mocked provider calls away from real budget state."""

from pathlib import Path

import pytest

from core import secrets
from features.tutor_agent import budget


@pytest.fixture(autouse=True)
def isolated_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(budget, "BUDGET_FILE", tmp_path / "budget_state.json")
    monkeypatch.setattr(secrets, "SECRETS_FILE", tmp_path / "secrets.json")
