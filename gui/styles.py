"""
Paleta de cores e folha de estilo global (QSS) do Roots Auto Doctor.
Mantém tudo num único ponto para que qualquer página use as mesmas cores.
"""

# ---- Paleta -----------------------------------------------------------

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

# ---- Folha de estilo global --------------------------------------------

APP_STYLE = f"""
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

/* Botões --------------------------------------------------------- */

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

QPushButton#primaryButton {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    color: #06181A;
}}
QPushButton#primaryButton:hover {{
    background: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton#primaryButton:disabled {{
    background: {CARD_BORDER};
    border-color: {CARD_BORDER};
    color: {TEXT_FAINT};
}}

QPushButton#dangerButton {{
    background: transparent;
    border: 1px solid {DANGER};
    color: {DANGER};
}}
QPushButton#dangerButton:hover {{
    background: rgba(255, 92, 108, 0.12);
}}

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
    background: {ACCENT_SOFT};
    color: {ACCENT};
}}

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
    background: {ACCENT_SOFT};
    border-color: {ACCENT};
    color: {ACCENT};
}}

/* Campos ----------------------------------------------------------- */

QLineEdit, QComboBox {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    selection-background-color: {ACCENT_SOFT};
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

/* Tabelas ------------------------------------------------------------ */

QTableWidget {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 10px;
    gridline-color: {DIVIDER};
    selection-background-color: {ACCENT_SOFT};
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

/* Scrollbars ---------------------------------------------------------- */

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
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
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
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QStatusBar {{
    background: {BG_TOPBAR};
    color: {TEXT_FAINT};
    border-top: 1px solid {DIVIDER};
}}

QLabel {{
    color: {TEXT};
}}
"""
