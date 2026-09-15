"""
Sistema central de temas do Roots Auto Doctor.

Responsabilidades:
- Paleta global da aplicação
- Temas predefinidos
- Persistência do tema
- Aplicação dinâmica do tema
- Comunicação do tema actual através do QApplication
- Construção do QSS global

A cor escolhida pelo utilizador é guardada em:
    appearance/accent
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor

from app.config import SETTINGS_ORGANISATION, SETTINGS_APPLICATION


# ============================================================================
# PALETA BASE
# ============================================================================

BG = "#0A0C10"
BG_SIDEBAR = "#0A0C10"
BG_TOPBAR = "#0D1015"

CARD_BG = "#12151B"
CARD_BG_HOVER = "#171B23"
CARD_BORDER = "#232833"
DIVIDER = "#1C2129"

TEXT = "#EDEFF3"
TEXT_DIM = "#9098A6"
TEXT_FAINT = "#5C6470"

ACCENT = "#22D3C9"
ACCENT_HOVER = "#3EE0D6"
ACCENT_PRESSED = "#17ADA4"
ACCENT_SOFT = "rgba(34, 211, 201, 0.14)"

SUCCESS = "#3DDC84"
WARNING = "#FFB454"
DANGER = "#FF5C6C"


# ============================================================================
# TEMAS
# ============================================================================

THEMES = {
    "Cyan": "#22D3C9",
    "Blue": "#4DA3FF",
    "Purple": "#A78BFA",
    "Green": "#45D483",
    "Orange": "#FF9F43",
    "Red": "#FF5C6C",
}


# ============================================================================
# ESTADO DO TEMA
# ============================================================================

DEFAULT_ACCENT = ACCENT

_LAST_ACCENT = DEFAULT_ACCENT


# ============================================================================
# SETTINGS
# ============================================================================

ACCENT_SETTINGS_KEY = "appearance/accent"


def get_settings() -> QSettings:
    """Retorna a instância central de QSettings."""

    return QSettings(
        SETTINGS_ORGANISATION,
        SETTINGS_APPLICATION,
    )


def normalize_accent(accent: Optional[str]) -> str:
    """
    Valida e normaliza uma cor hexadecimal.

    Valores inválidos voltam automaticamente ao tema predefinido.
    """

    if not isinstance(accent, str):
        return DEFAULT_ACCENT

    accent = accent.strip()

    color = QColor(accent)

    if not color.isValid():
        return DEFAULT_ACCENT

    return color.name().upper()


def get_saved_accent() -> str:
    """
    Obtém a cor guardada pelo utilizador.

    Se não existir ou estiver inválida, devolve a cor predefinida.
    """

    settings = get_settings()

    accent = settings.value(
        ACCENT_SETTINGS_KEY,
        DEFAULT_ACCENT,
    )

    return normalize_accent(accent)


def save_accent(accent: str) -> str:
    """
    Guarda a cor escolhida pelo utilizador.

    Devolve sempre a cor normalizada.
    """

    accent = normalize_accent(accent)

    settings = get_settings()

    settings.setValue(
        ACCENT_SETTINGS_KEY,
        accent,
    )

    settings.sync()

    return accent


def reset_accent() -> str:
    """Remove a preferência personalizada e restaura o tema original."""

    settings = get_settings()

    settings.remove(
        ACCENT_SETTINGS_KEY
    )

    settings.sync()

    return DEFAULT_ACCENT


# ============================================================================
# CORES DINÂMICAS
# ============================================================================

def _hex_to_rgb(accent: str) -> tuple[int, int, int]:
    """Converte HEX para RGB."""

    accent = normalize_accent(accent)

    return (
        int(accent[1:3], 16),
        int(accent[3:5], 16),
        int(accent[5:7], 16),
    )


def _rgba(accent: str, alpha: float) -> str:
    """Cria uma cor RGBA a partir de HEX."""

    r, g, b = _hex_to_rgb(accent)

    return f"rgba({r}, {g}, {b}, {alpha})"


def get_theme_colors(accent: Optional[str] = None) -> dict:
    """
    Retorna todas as cores dinâmicas do tema actual.

    Útil para widgets que precisam de construir estilos locais.
    """

    accent = normalize_accent(
        accent or get_saved_accent()
    )

    color = QColor(accent)

    hover = color.lighter(115).name().upper()
    pressed = color.darker(115).name().upper()

    return {
        "accent": accent,
        "accent_hover": hover,
        "accent_pressed": pressed,
        "accent_soft": _rgba(accent, 0.14),
        "accent_soft_light": _rgba(accent, 0.08),
        "accent_border": _rgba(accent, 0.35),
    }


# ============================================================================
# QSS
# ============================================================================

def build_app_style(accent: Optional[str] = None) -> str:
    """
    Constrói o QSS completo usando a cor de destaque fornecida.
    """

    accent = normalize_accent(
        accent or get_saved_accent()
    )

    colors = get_theme_colors(accent)

    accent_hover = colors["accent_hover"]
    accent_pressed = colors["accent_pressed"]
    accent_soft = colors["accent_soft"]

    return f"""
/* =========================================================================
   ROOTS AUTO DOCTOR
   Global Theme
   ========================================================================= */

QMainWindow {{
    background: {BG};
}}

QWidget {{
    color: {TEXT};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}

QToolTip {{
    background: {CARD_BG};
    color: {TEXT};
    border: 1px solid {CARD_BORDER};
    padding: 4px 8px;
    border-radius: 4px;
}}


/* =========================================================================
   BOTÕES
   ========================================================================= */

QPushButton {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
    color: {TEXT};
}}

QPushButton:hover {{
    background: {CARD_BG_HOVER};
    border-color: #2E3542;
}}

QPushButton:pressed {{
    background: #0F1217;
}}

QPushButton:disabled {{
    color: {TEXT_FAINT};
    background: {CARD_BG};
}}


/* Primary */

QPushButton#primaryButton {{
    background: {accent};
    border: 1px solid {accent};
    color: #06181A;
}}

QPushButton#primaryButton:hover {{
    background: {accent_hover};
    border-color: {accent_hover};
}}

QPushButton#primaryButton:pressed {{
    background: {accent_pressed};
}}

QPushButton#primaryButton:disabled {{
    background: {CARD_BORDER};
    border-color: {CARD_BORDER};
    color: {TEXT_FAINT};
}}


/* Danger */

QPushButton#dangerButton {{
    background: transparent;
    border: 1px solid {DANGER};
    color: {DANGER};
}}

QPushButton#dangerButton:hover {{
    background: rgba(255, 92, 108, 0.12);
}}


/* Navigation */

QPushButton#navButton {{
    text-align: left;
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 11px 14px;
    color: {TEXT_DIM};
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#navButton:hover {{
    background: {CARD_BG};
    color: {TEXT};
}}

QPushButton#navButton:checked {{
    background: {accent_soft};
    color: {accent};
}}


/* Category */

QPushButton#categoryChip {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 16px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 12px;
    color: {TEXT_DIM};
}}

QPushButton#categoryChip:hover {{
    background: {CARD_BG_HOVER};
    color: {TEXT};
}}

QPushButton#categoryChip:checked {{
    background: {accent_soft};
    border-color: {accent};
    color: {accent};
}}


/* =========================================================================
   CAMPOS
   ========================================================================= */

QLineEdit,
QComboBox {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {accent};
    selection-color: #06181A;
}}

QLineEdit:focus,
QComboBox:focus {{
    border: 1px solid {accent};
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox QAbstractItemView {{
    background: {CARD_BG};
    color: {TEXT};
    border: 1px solid {CARD_BORDER};
    selection-background-color: {accent_soft};
    selection-color: {TEXT};
    outline: none;
    padding: 4px;
}}

QTextEdit {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 10px;
    padding: 12px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}}


/* =========================================================================
   TABELAS
   ========================================================================= */

QTableWidget {{
    background: {CARD_BG};
    alternate-background-color: {CARD_BG_HOVER};
    border: 1px solid {CARD_BORDER};
    border-radius: 10px;
    gridline-color: {DIVIDER};
    selection-background-color: {accent_soft};
    selection-color: {TEXT};
}}

QTableWidget::item {{
    padding: 9px 6px;
    border-bottom: 1px solid {DIVIDER};
}}

QHeaderView::section {{
    background: {BG_TOPBAR};
    color: {TEXT_DIM};
    border: none;
    border-bottom: 1px solid {CARD_BORDER};
    padding: 10px 8px;
    font-weight: 700;
    font-size: 11px;
}}

QTableCornerButton::section {{
    background: {BG_TOPBAR};
    border: none;
}}


/* =========================================================================
   SCROLLBARS
   ========================================================================= */

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {CARD_BORDER};
    border-radius: 5px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_FAINT};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {CARD_BORDER};
    border-radius: 5px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {TEXT_FAINT};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}


/* =========================================================================
   TABS
   ========================================================================= */

QTabWidget {{
    background: transparent;
    border: none;
}}

QTabWidget::pane {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 12px;
    top: -1px;
}}

QTabBar {{
    background: transparent;
    border: none;
}}

QTabBar::tab {{
    background: transparent;
    color: {TEXT_DIM};
    border: 1px solid transparent;
    border-bottom: none;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    padding: 11px 20px;
    margin-right: 4px;
    min-width: 100px;
    font-size: 12px;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background: {CARD_BG};
    color: {TEXT};
    border-color: {CARD_BORDER};
}}

QTabBar::tab:selected {{
    background: {CARD_BG};
    color: {accent};
    border: 1px solid {CARD_BORDER};
    border-bottom: 2px solid {accent};
    font-weight: 800;
}}

QTabBar::tab:selected:hover {{
    color: {accent};
}}


/* =========================================================================
   CHECKBOXES
   ========================================================================= */

QCheckBox {{
    color: {TEXT};
    spacing: 9px;
}}

QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border-radius: 5px;
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
}}

QCheckBox::indicator:hover {{
    border-color: {accent};
}}

QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent};
}}


/* =========================================================================
   STATUS BAR
   ========================================================================= */

QStatusBar {{
    background: {BG_TOPBAR};
    color: {TEXT_FAINT};
    border-top: 1px solid {DIVIDER};
}}


/* =========================================================================
   LABELS
   ========================================================================= */

QLabel {{
    color: {TEXT};
}}
"""


# ============================================================================
# APPLY THEME
# ============================================================================

def apply_theme(app, accent: Optional[str]) -> str:
    """
    Aplica imediatamente o tema global.

    Importante:
    - actualiza o QSS global;
    - guarda a cor actual no QApplication;
    - mantém o último accent disponível;
    - permite que outros componentes consultem o tema actual.
    """

    global _LAST_ACCENT

    if app is None:
        return DEFAULT_ACCENT

    accent = normalize_accent(accent)

    app.setStyleSheet(
        build_app_style(accent)
    )

    # Estado global acessível por qualquer widget.
    app.setProperty(
        "rootsAccent",
        accent,
    )

    app.setProperty(
        "rootsTheme",
        get_theme_name(accent),
    )

    _LAST_ACCENT = accent

    return accent


def load_and_apply_saved_theme(app) -> str:
    """
    Carrega o tema guardado e aplica-o.

    Deve ser chamado o mais cedo possível no arranque da aplicação,
    idealmente antes de criar o Splash Screen.
    """

    accent = get_saved_accent()

    return apply_theme(
        app,
        accent,
    )


def set_accent(app, accent: str, persist: bool = True) -> str:
    """
    Altera o tema da aplicação.

    persist=True:
        Guarda a escolha para os próximos arranques.

    persist=False:
        Aplica apenas nesta sessão.
    """

    accent = normalize_accent(accent)

    if persist:
        save_accent(accent)

    return apply_theme(
        app,
        accent,
    )


def restore_default_theme(app) -> str:
    """Restaura o tema original e remove a preferência guardada."""

    accent = reset_accent()

    return apply_theme(
        app,
        accent,
    )


# ============================================================================
# INFORMAÇÃO DO TEMA
# ============================================================================

def get_theme_name(accent: Optional[str] = None) -> str:
    """Obtém o nome do preset correspondente à cor."""

    accent = normalize_accent(
        accent or get_saved_accent()
    )

    for name, value in THEMES.items():
        if normalize_accent(value) == accent:
            return name

    return "Personalizado"


def is_custom_theme(accent: Optional[str] = None) -> bool:
    """Indica se a cor actual é personalizada."""

    return get_theme_name(accent) == "Personalizado"


def get_current_accent() -> str:
    """Obtém a cor actualmente guardada."""

    return get_saved_accent()

