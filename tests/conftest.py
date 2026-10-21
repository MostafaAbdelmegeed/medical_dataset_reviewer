"""Keep tests independent of local application preferences."""

import pytest
from seg_qc_tool import controller


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(controller, "CONFIG_PATH", tmp_path / "config.json")
