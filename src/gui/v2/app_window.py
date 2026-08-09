"""Shell principal Fluent 2.0 construido sobre la lógica existente."""

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, FluentWindow, NavigationItemPosition

from src.gui.v2.pages.activity_page import ActivityPage
from src.gui.v2.pages.feature_pages import (
    DisksPage,
    DuplicatesPage,
    MusicPage,
)
from src.gui.v2.pages.home_page import HomePage
from src.gui.v2.pages.legacy_page import LegacyPage
from src.gui.v2.pages.organize_page import OrganizePage
from src.gui.v2.pages.settings_page import SettingsPage
from src.gui.v2.theme import apply_fluent_theme


class FluentAppWindow(FluentWindow):
    """Ventana V2 con navegación lateral y páginas migradas progresivamente."""

    def __init__(self, legacy_window, parent=None):
        super().__init__(parent)
        self.legacy_window = legacy_window
        self.config = legacy_window.app_config
        self._routes: dict[str, QWidget] = {}
        self._legacy_pages: dict[str, LegacyPage] = {}

        self.setObjectName("fluentAppWindow")
        self.setWindowTitle("Ordenasion 2.0")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        apply_fluent_theme(self.config)

        self._detach_legacy_pages()
        self._build_navigation()
        self._connect_controller()
        self._setup_shortcuts()

        self.legacy_window.hide()

    def _detach_legacy_pages(self) -> None:
        """Extrae las pestañas actuales para reutilizarlas como contenido V2."""
        tabs = self.legacy_window.main_tabs
        tabs.blockSignals(True)
        self._legacy_widgets: dict[str, QWidget] = {}
        routes = ("organize", "disks", "music", "duplicates", "legacy_log")
        for route in routes:
            if tabs.count() == 0:
                break
            widget = tabs.widget(0)
            tabs.removeTab(0)
            widget.setParent(None)
            self._legacy_widgets[route] = widget
        tabs.blockSignals(False)

    def _build_navigation(self) -> None:
        home = HomePage(self.config, self.legacy_window.profile_manager)
        self._add_route("home", home, FluentIcon.HOME, "Inicio")
        home.navigate_requested.connect(self._switch_route)
        home.analyze_requested.connect(self._analyze_from_home)

        organize = OrganizePage(
            self._legacy_widgets["organize"],
            self.config,
            self.legacy_window,
        )
        disks = DisksPage(self._legacy_widgets["disks"], self.config)
        music = MusicPage(self._legacy_widgets["music"], self.config)
        duplicates = DuplicatesPage(
            self._legacy_widgets["duplicates"],
            self.config,
        )
        for route, page, icon, title in (
            ("organize", organize, FluentIcon.FOLDER, "Organizar"),
            ("disks", disks, FluentIcon.SAVE_AS, "Discos"),
            ("music", music, FluentIcon.MUSIC, "Música"),
            ("duplicates", duplicates, FluentIcon.COPY, "Duplicados"),
        ):
            self._legacy_pages[route] = page
            self._add_route(route, page, icon, title)

        activity = ActivityPage(
            self.legacy_window,
            self.legacy_window.log_text,
        )
        self._add_route("activity", activity, FluentIcon.SYNC, "Actividad")

        settings = SettingsPage(self.config)
        settings.advanced_settings_requested.connect(
            self.legacy_window.open_configuration
        )
        settings.theme_changed.connect(self._refresh_theme)
        self._add_route(
            "settings",
            settings,
            FluentIcon.SETTING,
            "Configuración",
            NavigationItemPosition.BOTTOM,
        )

        self.switchTo(self._routes["home"])

    def _add_route(
        self,
        route: str,
        page: QWidget,
        icon,
        title: str,
        position: NavigationItemPosition = NavigationItemPosition.TOP,
    ) -> None:
        page.setObjectName(route)
        self._routes[route] = page
        self.addSubInterface(page, icon, title, position)

    def _connect_controller(self) -> None:
        self.legacy_window.disk_viewer.disk_selected.connect(
            lambda _path: self._switch_route("organize")
        )

    def _setup_shortcuts(self) -> None:
        shortcuts: tuple[tuple[str, str], ...] = (
            ("Ctrl+1", "home"),
            ("Ctrl+2", "organize"),
            ("Ctrl+3", "disks"),
            ("Ctrl+4", "music"),
            ("Ctrl+5", "duplicates"),
            ("Ctrl+6", "activity"),
            ("Ctrl+7", "settings"),
        )
        for sequence, route in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(
                lambda destination=route: self._switch_route(destination)
            )

    def _switch_route(self, route: str) -> None:
        page = self._routes.get(route)
        if page is not None:
            self.switchTo(page)

    def _analyze_from_home(self, path: str) -> None:
        self._switch_route("organize")
        self.legacy_window.folder_input.setText(path)
        self.legacy_window.start_analysis()

    def _refresh_theme(self) -> None:
        apply_fluent_theme(self.config)
        for page in self._legacy_pages.values():
            page.refresh_theme(self.config)
        self.legacy_window.log_message("Tema Fluent actualizado")

    def closeEvent(self, event) -> None:
        self.legacy_window.close()
        super().closeEvent(event)
