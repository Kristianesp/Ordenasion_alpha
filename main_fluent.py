#!/usr/bin/env python3
"""Punto de entrada experimental de Ordenasion 2.0 Fluent."""

import sys

from PyQt6.QtWidgets import QApplication

from src.gui.main_window import FileOrganizerGUI
from src.gui.v2.app_window import FluentAppWindow


def main() -> int:
    app = QApplication(sys.argv)
    legacy_window = FileOrganizerGUI()
    window = FluentAppWindow(legacy_window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
