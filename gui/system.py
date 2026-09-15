from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QTabWidget,
    QColorDialog,
    QComboBox,
    QCheckBox,
    QApplication,
)

from gui.connection import ConnectionPage
from gui.widgets import page_header
from gui.styles import (
    ACCENT,
    CARD_BG,
    CARD_BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    THEMES,
    set_accent,
    restore_default_theme,
    get_current_accent,
)


class AppearancePage(QWidget):
    """Página de aparência da aplicação."""

    accent_changed = Signal(str)

    def __init__(self, settings=None):
        super().__init__()

        self.settings = settings or QSettings(
            "RootsAutoDoctor",
            "Roots Auto Doctor",
        )

        self._building_ui = True

        self._build_ui()
        self._load_settings()

        self._building_ui = False

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(
            page_header(
                "Aparência",
                "Personaliza a identidade visual do Roots Auto Doctor.",
            )
        )

        # --------------------------------------------------------------
        # Accent card
        # --------------------------------------------------------------

        accent_card = self._create_card()

        accent_layout = QVBoxLayout(accent_card)
        accent_layout.setContentsMargins(22, 20, 22, 22)
        accent_layout.setSpacing(16)

        title = QLabel("COR DE DESTAQUE")
        title.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 800;
            color: {TEXT_DIM};
            letter-spacing: 1.4px;
            """
        )

        accent_layout.addWidget(title)

        description = QLabel(
            "Define a cor utilizada nos botões, indicadores, menus "
            "e restantes elementos activos da interface."
        )

        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 12px;"
        )

        accent_layout.addWidget(description)

        # --------------------------------------------------------------
        # Presets
        # --------------------------------------------------------------

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumHeight(40)

        for name, color in THEMES.items():
            self.theme_combo.addItem(name, color)

        self.theme_combo.currentIndexChanged.connect(
            self._preset_changed
        )

        accent_layout.addWidget(self.theme_combo)

        # --------------------------------------------------------------
        # Custom color
        # --------------------------------------------------------------

        custom_row = QHBoxLayout()
        custom_row.setSpacing(12)

        custom_text = QVBoxLayout()
        custom_text.setSpacing(2)

        custom_label = QLabel("Cor personalizada")
        custom_label.setStyleSheet(
            f"color: {TEXT}; font-weight: 600;"
        )

        custom_hint = QLabel(
            "Escolhe qualquer cor através do selector."
        )

        custom_hint.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 11px;"
        )

        custom_text.addWidget(custom_label)
        custom_text.addWidget(custom_hint)

        custom_row.addLayout(custom_text)
        custom_row.addStretch()

        self.custom_button = QPushButton("Escolher cor")
        self.custom_button.setCursor(Qt.PointingHandCursor)
        self.custom_button.setMinimumHeight(38)

        self.custom_button.clicked.connect(
            self.choose_custom
        )

        custom_row.addWidget(self.custom_button)

        accent_layout.addLayout(custom_row)

        # --------------------------------------------------------------
        # Preview
        # --------------------------------------------------------------

        preview_title = QLabel("PRÉ-VISUALIZAÇÃO")
        preview_title.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 800;
            color: {TEXT_DIM};
            letter-spacing: 1.4px;
            """
        )

        accent_layout.addWidget(preview_title)

        self.preview = QFrame()
        self.preview.setObjectName("appearancePreview")
        self.preview.setMinimumHeight(86)

        preview_layout = QVBoxLayout(self.preview)
        preview_layout.setContentsMargins(16, 14, 16, 14)
        preview_layout.setSpacing(8)

        preview_header = QHBoxLayout()

        self.preview_status = QLabel(
            "● SISTEMA PRONTO"
        )

        preview_status = self.preview_status

        preview_status.setStyleSheet(
            "font-size: 11px; font-weight: 800;"
        )

        preview_header.addWidget(preview_status)
        preview_header.addStretch()

        preview_layout.addLayout(preview_header)

        self.preview_text = QLabel(
            "Roots Auto Doctor — pré-visualização da interface"
        )

        self.preview_text.setStyleSheet(
            f"color: {TEXT}; font-size: 12px;"
        )

        preview_layout.addWidget(
            self.preview_text
        )

        accent_layout.addWidget(
            self.preview
        )

        layout.addWidget(
            accent_card
        )

        # --------------------------------------------------------------
        # Reset
        # --------------------------------------------------------------

        actions = QHBoxLayout()

        restart_hint = QLabel(
            "Alguns elementos (dashboard, mostradores) só refletem "
            "a nova cor por completo depois de reiniciares a app."
        )
        restart_hint.setWordWrap(True)
        restart_hint.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 11px;"
        )
        actions.addWidget(restart_hint, 1)

        self.reset_button = QPushButton(
            "Restaurar predefinições"
        )

        self.reset_button.setCursor(
            Qt.PointingHandCursor
        )

        self.reset_button.clicked.connect(
            self.reset_defaults
        )

        actions.addWidget(
            self.reset_button
        )

        layout.addLayout(actions)
        layout.addStretch()

        self._update_preview(
            get_current_accent()
        )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _load_settings(self):
        accent = get_current_accent()

        index = self.theme_combo.findData(
            accent
        )

        self.theme_combo.blockSignals(True)

        if index >= 0:
            self.theme_combo.setCurrentIndex(
                index
            )
        else:
            self.theme_combo.setCurrentIndex(-1)

        self.theme_combo.blockSignals(False)

        self._set_custom_button_color(
            accent
        )

        self._update_preview(
            accent
        )

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def _preset_changed(self, index):
        if self._building_ui:
            return

        accent = self.theme_combo.itemData(
            index
        )

        if not accent:
            return

        self._apply_accent(
            accent
        )

    # ------------------------------------------------------------------
    # Custom color
    # ------------------------------------------------------------------

    def choose_custom(self):

        current = get_current_accent()

        current_color = QColor(
            current
        )

        if not current_color.isValid():
            current_color = QColor(
                ACCENT
            )

        color = QColorDialog.getColor(
            current_color,
            self,
            "Escolher cor de destaque",
        )

        if not color.isValid():
            return

        accent = color.name().upper()

        self._apply_accent(
            accent
        )

        self.theme_combo.blockSignals(
            True
        )

        self.theme_combo.setCurrentIndex(
            -1
        )

        self.theme_combo.blockSignals(
            False
        )

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def _apply_accent(self, accent):

        color = QColor(
            accent
        )

        if not color.isValid():
            accent = ACCENT

        accent = accent.upper()

        qapp = QApplication.instance()

        if qapp is not None:
            set_accent(
                qapp,
                accent,
                persist=True,
            )

        self._set_custom_button_color(
            accent
        )

        self._update_preview(
            accent
        )

        self.accent_changed.emit(
            accent
        )

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self, accent):

        color = QColor(
            accent
        )

        if not color.isValid():
            color = QColor(
                ACCENT
            )

        hex_color = color.name().upper()

        self.preview.setStyleSheet(
            f"""
            #appearancePreview {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 12px;
            }}
            """
        )

        self.preview_status.setStyleSheet(
            f"""
            color: {hex_color};
            font-size: 11px;
            font-weight: 800;
            """
        )

        self._set_custom_button_color(
            hex_color
        )

    def _set_custom_button_color(self, accent):

        color = QColor(
            accent
        )

        if not color.isValid():
            color = QColor(
                ACCENT
            )

        self.custom_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {color.name()};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: {color.lighter(115).name()};
            }}

            QPushButton:pressed {{
                background: {color.darker(110).name()};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_defaults(self):

        app = QApplication.instance()

        if app is not None:
            restore_default_theme(
                app
            )

        accent = get_current_accent()

        index = self.theme_combo.findData(
            accent
        )

        self.theme_combo.blockSignals(
            True
        )

        if index >= 0:
            self.theme_combo.setCurrentIndex(
                index
            )
        else:
            self.theme_combo.setCurrentIndex(
                -1
            )

        self.theme_combo.blockSignals(
            False
        )

        self._set_custom_button_color(
            accent
        )

        self._update_preview(
            accent
        )

        self.accent_changed.emit(
            accent
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_card():

        card = QFrame()
        card.setObjectName(
            "settingsCard"
        )

        card.setStyleSheet(
            f"""
            #settingsCard {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 14px;
            }}
            """
        )

        return card


class PreferencesPage(QWidget):
    """Preferências gerais da aplicação."""

    def __init__(self, settings=None):
        super().__init__()

        self.settings = settings or QSettings(
            "RootsAutoDoctor",
            "Roots Auto Doctor",
        )

        self._build_ui()
        self._load_settings()

    def _build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(16)

        # --------------------------------------------------------------
        # General
        # --------------------------------------------------------------

        general_card = QFrame()
        general_card.setObjectName(
            "preferencesCard"
        )

        general_card.setStyleSheet(
            f"""
            #preferencesCard {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 14px;
            }}
            """
        )

        box = QVBoxLayout(
            general_card
        )

        box.setContentsMargins(
            22,
            20,
            22,
            22,
        )

        box.setSpacing(14)

        title = QLabel(
            "PREFERÊNCIAS GERAIS"
        )

        title.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 800;
            color: {TEXT_DIM};
            letter-spacing: 1.4px;
            """
        )

        box.addWidget(title)

        description = QLabel(
            "Define o comportamento geral do Roots Auto Doctor."
        )

        description.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 12px;"
        )

        description.setWordWrap(True)

        box.addWidget(description)

        self.startup_check = QCheckBox(
            "Iniciar automaticamente com o sistema"
        )

        self.confirm_exit_check = QCheckBox(
            "Confirmar antes de fechar a aplicação"
        )

        self.save_history_check = QCheckBox(
            "Guardar histórico de diagnósticos"
        )

        for checkbox in (
            self.startup_check,
            self.confirm_exit_check,
            self.save_history_check,
        ):
            checkbox.setCursor(
                Qt.PointingHandCursor
            )

            box.addWidget(
                checkbox
            )

        layout.addWidget(
            general_card
        )

        # --------------------------------------------------------------
        # Diagnostic units
        # --------------------------------------------------------------

        units_card = QFrame()
        units_card.setObjectName(
            "unitsCard"
        )

        units_card.setStyleSheet(
            f"""
            #unitsCard {{
                background: {CARD_BG};
                border: 1px solid {CARD_BORDER};
                border-radius: 14px;
            }}
            """
        )

        units_layout = QGridLayout(
            units_card
        )

        units_layout.setContentsMargins(
            22,
            20,
            22,
            22,
        )

        units_layout.setHorizontalSpacing(
            20
        )

        units_layout.setVerticalSpacing(
            14
        )

        units_title = QLabel(
            "UNIDADES DE DIAGNÓSTICO"
        )

        units_title.setStyleSheet(
            f"""
            font-size: 11px;
            font-weight: 800;
            color: {TEXT_DIM};
            letter-spacing: 1.4px;
            """
        )

        units_layout.addWidget(
            units_title,
            0,
            0,
            1,
            2,
        )

        temp_label = QLabel(
            "Temperatura"
        )

        temp_label.setStyleSheet(
            f"color: {TEXT}; font-weight: 600;"
        )

        self.temperature_combo = QComboBox()

        self.temperature_combo.addItems(
            [
                "°C",
                "°F",
            ]
        )

        pressure_label = QLabel(
            "Pressão"
        )

        pressure_label.setStyleSheet(
            f"color: {TEXT}; font-weight: 600;"
        )

        self.pressure_combo = QComboBox()

        self.pressure_combo.addItems(
            [
                "bar",
                "PSI",
                "kPa",
            ]
        )

        units_layout.addWidget(
            temp_label,
            1,
            0,
        )

        units_layout.addWidget(
            self.temperature_combo,
            1,
            1,
        )

        units_layout.addWidget(
            pressure_label,
            2,
            0,
        )

        units_layout.addWidget(
            self.pressure_combo,
            2,
            1,
        )

        layout.addWidget(
            units_card
        )

        layout.addStretch()

        # --------------------------------------------------------------
        # Persistence
        # --------------------------------------------------------------

        self.startup_check.stateChanged.connect(
            lambda state: self._save_bool(
                "preferences/startup",
                state,
            )
        )

        self.confirm_exit_check.stateChanged.connect(
            lambda state: self._save_bool(
                "preferences/confirm_exit",
                state,
            )
        )

        self.save_history_check.stateChanged.connect(
            lambda state: self._save_bool(
                "preferences/save_history",
                state,
            )
        )

        self.temperature_combo.currentTextChanged.connect(
            lambda value: self._save_value(
                "preferences/temperature_unit",
                value,
            )
        )

        self.pressure_combo.currentTextChanged.connect(
            lambda value: self._save_value(
                "preferences/pressure_unit",
                value,
            )
        )

    def _load_settings(self):

        self.startup_check.setChecked(
            self._read_bool(
                "preferences/startup",
                False,
            )
        )

        self.confirm_exit_check.setChecked(
            self._read_bool(
                "preferences/confirm_exit",
                True,
            )
        )

        self.save_history_check.setChecked(
            self._read_bool(
                "preferences/save_history",
                True,
            )
        )

        self.temperature_combo.setCurrentText(
            self.settings.value(
                "preferences/temperature_unit",
                "°C",
            )
        )

        self.pressure_combo.setCurrentText(
            self.settings.value(
                "preferences/pressure_unit",
                "bar",
            )
        )

    def _read_bool(
        self,
        key,
        default,
    ):

        value = self.settings.value(
            key,
            default,
        )

        if isinstance(value, bool):
            return value

        return str(value).lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def _save_bool(
        self,
        key,
        state,
    ):

        self.settings.setValue(
            key,
            bool(state),
        )

        self.settings.sync()

    def _save_value(
        self,
        key,
        value,
    ):

        self.settings.setValue(
            key,
            value,
        )

        self.settings.sync()


class SystemPage(QWidget):
    """Centro de sistema do Roots Auto Doctor.

    Centraliza:
        - Ligação ao veículo
        - Aparência
        - Preferências gerais
    """

    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "RootsAutoDoctor",
            "Roots Auto Doctor",
        )

        self._build_ui()

    def _build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(16)

        layout.addWidget(
            page_header(
                "Sistema",
                "Ligação, aparência e preferências do Roots Auto Doctor.",
            )
        )

        # --------------------------------------------------------------
        # Tabs
        # --------------------------------------------------------------

        self.tabs = QTabWidget()

        self.tabs.setDocumentMode(
            True
        )

        self.tabs.setObjectName(
            "systemTabs"
        )

        # O estilo das tabs é agora controlado pelo styles.py.
        # Não colocamos cores aqui para evitar que fiquem
        # dessincronizadas quando o utilizador muda o tema.

        # --------------------------------------------------------------
        # Pages
        # --------------------------------------------------------------

        self.connection_page = ConnectionPage()

        self.appearance_page = AppearancePage(
            settings=self.settings
        )

        self.preferences_page = PreferencesPage(
            settings=self.settings
        )

        # --------------------------------------------------------------
        # Add tabs
        # --------------------------------------------------------------

        self.tabs.addTab(
            self.connection_page,
            "Ligação",
        )

        self.tabs.addTab(
            self.appearance_page,
            "Aparência",
        )

        self.tabs.addTab(
            self.preferences_page,
            "Preferências",
        )

        # --------------------------------------------------------------
        # Layout
        # --------------------------------------------------------------

        layout.addWidget(
            self.tabs,
            1,
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def show_connection(self):
        """Abre directamente a secção de ligação."""

        self.tabs.setCurrentWidget(
            self.connection_page
        )

    def show_appearance(self):
        """Abre directamente a secção de aparência."""

        self.tabs.setCurrentWidget(
            self.appearance_page
        )

    def show_preferences(self):
        """Abre directamente a secção de preferências."""

        self.tabs.setCurrentWidget(
            self.preferences_page
        )

