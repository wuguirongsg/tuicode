from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_tuicode_data_home(tmp_path, monkeypatch):
    """Keep persistent session-memory tests out of the user's real data dir."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))
