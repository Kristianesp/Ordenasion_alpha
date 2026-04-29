import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import src.gui.main_window as main_window_module


class _FakeLineEdit:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


def test_schedule_post_organization_refresh_triggers_analysis(monkeypatch, tmp_path):
    scheduled = {}
    logs = []

    def _fake_single_shot(delay, callback):
        scheduled["delay"] = delay
        scheduled["callback"] = callback

    fake_self = SimpleNamespace(
        folder_input=_FakeLineEdit(str(tmp_path)),
        log_message=lambda message: logs.append(message),
        start_analysis=lambda: None,
    )

    monkeypatch.setattr(main_window_module.QTimer, "singleShot", _fake_single_shot)

    main_window_module.FileOrganizerGUI._schedule_post_organization_refresh(fake_self)

    assert scheduled["delay"] == 150
    assert scheduled["callback"] == fake_self.start_analysis
    assert logs[-1] == "🔄 Refrescando resultados tras la organización..."
