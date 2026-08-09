"""Página de inicio de la interfaz Fluent."""

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SubtitleLabel,
)

from src.gui.task_center import task_registry
from src.gui.v2.components import FeatureCard, MetricCard, PageHeader
from src.utils.app_config import AppConfig


class HomePage(ScrollArea):
    """Resumen operativo y accesos rápidos."""

    navigate_requested = pyqtSignal(str)
    analyze_requested = pyqtSignal(str)

    def __init__(self, config: AppConfig, profile_manager, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.config = config
        self.profile_manager = profile_manager
        self.setWidgetResizable(True)
        self.setFrameShape(ScrollArea.Shape.NoFrame)
        self.enableTransparentBackground()

        self.content = QWidget()
        self.content.setObjectName("homeContent")
        self.setWidget(self.content)
        self._build_ui()
        task_registry.tasks_updated.connect(self.refresh_metrics)
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(32, 26, 32, 32)
        layout.setSpacing(22)

        header = PageHeader(
            "Buenos días",
            "Todo lo importante de tu organización, discos y biblioteca en un solo lugar.",
            "Analizar carpeta",
            FluentIcon.SEARCH,
        )
        header.primary_clicked.connect(self._choose_folder)
        layout.addWidget(header)

        quick_card = CardWidget()
        quick_layout = QVBoxLayout(quick_card)
        quick_layout.setContentsMargins(20, 18, 20, 18)
        quick_layout.setSpacing(12)
        quick_layout.addWidget(SubtitleLabel("Organización rápida"))
        quick_layout.addWidget(
            BodyLabel(
                "Elige una carpeta. Primero analizaremos su contenido y siempre podrás revisar los cambios antes de mover nada."
            )
        )

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.recent_paths = ComboBox()
        self.recent_paths.setAccessibleName("Rutas recientes")
        self.recent_paths.setMinimumWidth(210)
        self.recent_paths.currentTextChanged.connect(self._use_recent_path)
        path_row.addWidget(self.recent_paths)
        self.path_input = LineEdit()
        self.path_input.setAccessibleName("Ruta de carpeta para analizar")
        self.path_input.setPlaceholderText("Ruta de la carpeta que quieres organizar")
        self.path_input.setClearButtonEnabled(True)
        path_row.addWidget(self.path_input, 1)
        browse_button = PushButton(FluentIcon.FOLDER, "Examinar")
        browse_button.setAccessibleName("Examinar carpetas")
        browse_button.clicked.connect(self._choose_folder)
        path_row.addWidget(browse_button)
        analyze_button = PrimaryPushButton(FluentIcon.SEARCH, "Analizar ahora")
        analyze_button.setAccessibleName("Analizar carpeta ahora")
        analyze_button.clicked.connect(self._analyze)
        path_row.addWidget(analyze_button)
        quick_layout.addLayout(path_row)
        layout.addWidget(quick_card)

        layout.addWidget(SubtitleLabel("Estado de un vistazo"))
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        self.recent_metric = MetricCard(
            FluentIcon.HISTORY,
            "Rutas recientes",
            "0",
            "Accesos rápidos guardados",
        )
        self.profile_metric = MetricCard(
            FluentIcon.PEOPLE,
            "Perfiles",
            "0",
            "Configuraciones listas para reutilizar",
        )
        self.task_metric = MetricCard(
            FluentIcon.SYNC,
            "Actividad",
            "Sin tareas",
            "Procesos en segundo plano",
        )
        self.safety_metric = MetricCard(
            FluentIcon.COMPLETED,
            "Protección",
            "Siempre activa",
            "Preview, conflictos y deshacer",
        )
        for index, card in enumerate(
            (
                self.recent_metric,
                self.profile_metric,
                self.task_metric,
                self.safety_metric,
            )
        ):
            metrics.addWidget(card, index // 2, index % 2)
        layout.addLayout(metrics)

        layout.addWidget(SubtitleLabel("Explora las herramientas"))
        feature_grid = QGridLayout()
        feature_grid.setHorizontalSpacing(12)
        feature_grid.setVerticalSpacing(12)
        features = (
            (
                "organize",
                FluentIcon.FOLDER,
                "Organización segura",
                "Clasifica miles de archivos con vista previa, políticas de conflicto y rollback.",
                "Abrir Organizar",
            ),
            (
                "disks",
                FluentIcon.SAVE_AS,
                "Salud de discos",
                "Consulta uso, temperatura y métricas SMART sin salir de la aplicación.",
                "Abrir Discos",
            ),
            (
                "duplicates",
                FluentIcon.COPY,
                "Espacio recuperable",
                "Encuentra duplicados con modos rápido, híbrido y profundo.",
                "Abrir Duplicados",
            ),
            (
                "music",
                FluentIcon.MUSIC,
                "Biblioteca inteligente",
                "Indexa música, compara calidad, reproduce pistas y mejora sus metadatos.",
                "Abrir Música",
            ),
        )
        for index, (route, icon, title, description, action) in enumerate(features):
            card = FeatureCard(icon, title, description, action)
            card.activated.connect(
                lambda checked=False, destination=route: self.navigate_requested.emit(
                    destination
                )
            )
            feature_grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(feature_grid)
        layout.addStretch()

    def refresh(self) -> None:
        paths = self.config.get_recent_paths()
        favorites = self.config.get_favorite_paths()
        merged_paths = list(dict.fromkeys(favorites + paths))
        current_path = self.path_input.text()
        self.recent_paths.blockSignals(True)
        self.recent_paths.clear()
        self.recent_paths.addItem("Rutas recientes")
        self.recent_paths.addItems(merged_paths)
        self.recent_paths.blockSignals(False)
        if current_path:
            self.path_input.setText(current_path)
        self.refresh_metrics()

    def refresh_metrics(self) -> None:
        recent_count = len(self.config.get_recent_paths())
        profile_count = len(self.profile_manager.get_profile_names())
        tasks = task_registry.get_tasks()
        active = sum(
            1 for _, task in tasks if task.get("status") == "En progreso"
        )
        self.recent_metric.set_value(str(recent_count))
        self.profile_metric.set_value(str(profile_count))
        self.task_metric.set_value(
            f"{active} en curso" if active else "Sin tareas",
            f"{len(tasks)} tareas registradas",
        )

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecciona una carpeta para analizar",
            self.path_input.text() or str(Path.home()),
        )
        if folder:
            self.path_input.setText(folder)

    def _use_recent_path(self, path: str) -> None:
        if path and path != "Rutas recientes":
            self.path_input.setText(path)

    def _analyze(self) -> None:
        path = self.path_input.text().strip()
        if path:
            self.analyze_requested.emit(path)
