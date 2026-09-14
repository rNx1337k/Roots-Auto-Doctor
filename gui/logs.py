from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel
)

from gui.widgets import page_header
from gui.styles import TEXT_FAINT

# Limite de linhas guardadas em memória — evita que uma sessão longa
# de diagnóstico deixe o registo (e a app) cada vez mais lento.
MAX_LINES = 2000
TRIM_TO = 1500


class LogsPage(QWidget):

    def __init__(self):

        super().__init__()

        self._line_count = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header_row = QHBoxLayout()

        header_row.addWidget(page_header(
            "Registo de Comunicação",
            "Trama a trama, tudo o que é enviado e recebido da centralina."
        ), 1)

        self.count_label = QLabel("0 linhas")
        self.count_label.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 12px;"
        )
        header_row.addWidget(self.count_label, 0, Qt.AlignVCenter)

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

        clear_button.clicked.connect(self.clear_log)

        layout.addWidget(self.log)

    def append_line(self, line):

        self.log.append(line)
        self._line_count += 1

        # Corta o histórico mais antigo quando cresce demasiado, mantendo
        # sempre as linhas mais recentes visíveis.
        if self._line_count > MAX_LINES:

            document = self.log.document()
            excess = self._line_count - TRIM_TO

            cursor = self.log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(
                cursor.MoveOperation.Down,
                cursor.MoveMode.KeepAnchor,
                excess
            )
            cursor.removeSelectedText()

            self._line_count = document.blockCount() - 1

        self.count_label.setText(f"{self._line_count} linhas")

    def clear_log(self):
        self.log.clear()
        self._line_count = 0
        self.count_label.setText("0 linhas")
