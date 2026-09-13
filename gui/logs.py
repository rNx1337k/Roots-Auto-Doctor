from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton
)

from gui.widgets import page_header


class LogsPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header_row = QHBoxLayout()

        header_row.addWidget(page_header(
            "Registo de Comunicação",
            "Trama a trama, tudo o que é enviado e recebido da centralina."
        ), 1)

        clear_button = QPushButton("🗑   Limpar")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.setMinimumHeight(36)
        header_row.addWidget(clear_button, 0, Qt.AlignTop)

        layout.addLayout(header_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(
            "O tráfego de comunicação com a centralina vai aparecer aqui..."
        )

        clear_button.clicked.connect(self.log.clear)

        layout.addWidget(self.log)

    def append_line(self, line):
        self.log.append(line)
