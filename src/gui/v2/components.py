"""Componentes compartidos de la interfaz Fluent 2.0."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    IconWidget,
    PrimaryPushButton,
    SubtitleLabel,
    TitleLabel,
    TransparentToolButton,
)


class PageHeader(QWidget):
    """Cabecera consistente para todas las páginas."""

    primary_clicked = pyqtSignal()
    secondary_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        primary_text: str = "",
        primary_icon=None,
        secondary_icon=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = TitleLabel(title)
        self.subtitle_label = BodyLabel(subtitle)
        self.subtitle_label.setTextColor("#6B6B6B", "#C7C7C7")
        self.subtitle_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        layout.addLayout(text_layout, 1)

        self.secondary_button = TransparentToolButton()
        if secondary_icon is not None:
            self.secondary_button.setIcon(secondary_icon)
        self.secondary_button.setAccessibleName("Acción secundaria")
        self.secondary_button.setVisible(secondary_icon is not None)
        self.secondary_button.clicked.connect(self.secondary_clicked.emit)
        layout.addWidget(self.secondary_button)

        self.primary_button = PrimaryPushButton()
        if primary_icon is not None:
            self.primary_button.setIcon(primary_icon)
        self.primary_button.setText(primary_text)
        self.primary_button.setAccessibleName(primary_text or "Acción principal")
        self.primary_button.setVisible(bool(primary_text))
        self.primary_button.clicked.connect(self.primary_clicked.emit)
        layout.addWidget(self.primary_button)


class MetricCard(CardWidget):
    """Tarjeta compacta para una métrica o estado relevante."""

    def __init__(self, icon, title: str, value: str, detail: str, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(126)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.icon_widget = IconWidget(icon)
        self.icon_widget.setFixedSize(24, 24)
        header.addWidget(self.icon_widget)
        self.title_label = BodyLabel(title)
        header.addWidget(self.title_label)
        header.addStretch()
        layout.addLayout(header)

        self.value_label = SubtitleLabel(value)
        layout.addWidget(self.value_label)
        self.detail_label = CaptionLabel(detail)
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)

    def set_value(self, value: str, detail: str | None = None) -> None:
        self.value_label.setText(value)
        if detail is not None:
            self.detail_label.setText(detail)


class FeatureCard(CardWidget):
    """Tarjeta navegable que explica una fortaleza de la aplicación."""

    activated = pyqtSignal()

    def __init__(self, icon, title: str, description: str, action: str, parent=None):
        super().__init__(parent)
        self.setClickEnabled(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(118)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 16, 16)
        layout.setSpacing(14)

        icon_widget = IconWidget(icon)
        icon_widget.setFixedSize(30, 30)
        layout.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        title_label = SubtitleLabel(title)
        description_label = BodyLabel(description)
        description_label.setWordWrap(True)
        action_label = CaptionLabel(action)
        text_layout.addWidget(title_label)
        text_layout.addWidget(description_label)
        text_layout.addStretch()
        text_layout.addWidget(action_label)
        layout.addLayout(text_layout, 1)

        self.clicked.connect(self.activated.emit)
