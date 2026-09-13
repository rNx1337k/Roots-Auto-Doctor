from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from gui.widgets import page_header
from gui.styles import CARD_BG, CARD_BORDER, TEXT_DIM, TEXT_FAINT


class GraphsPage(QWidget):
    """A monitorização gráfica ao vivo já está integrada na página
    'Dados em Tempo Real' (tabela + gráfico lado a lado). Esta página
    fica como atalho/explicação e para futuras vistas multi-gráfico."""

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header(
            "Gráficos",
            "A monitorização gráfica ao vivo faz-se na página "
            "\"Dados em Tempo Real\" — seleciona um parâmetro e clica "
            "no ícone 📈 na respetiva linha."
        ))

        placeholder = QFrame()
        placeholder.setObjectName("placeholder")
        placeholder.setMinimumHeight(320)

        placeholder.setStyleSheet(f"""
        #placeholder {{
            background: {CARD_BG};
            border: 1px dashed {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

        inner = QVBoxLayout(placeholder)
        inner.setAlignment(Qt.AlignCenter)
        inner.setSpacing(8)

        icon = QLabel("📈")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 34px; background: transparent;")

        message = QLabel("Vai a \"Dados em Tempo Real\" para veres o "
                          "gráfico ao vivo de qualquer parâmetro.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 13px; background: transparent;"
        )

        inner.addWidget(icon)
        inner.addWidget(message)

        layout.addWidget(placeholder)
        layout.addStretch()
