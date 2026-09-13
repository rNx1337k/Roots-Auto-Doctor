from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QPushButton,
    QMessageBox
)

from gui.widgets import page_header, empty_hint, page_with_gate
from gui.styles import CARD_BG, CARD_BORDER, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER


class MonitorTile(QFrame):

    def __init__(self, name):

        super().__init__()

        self.setObjectName("monitorTile")
        self.setStyleSheet(f"""
        #monitorTile {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 10px;
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        self.name_label = QLabel(name)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {TEXT}; background: transparent;"
        )

        self.status_label = QLabel("—")
        self.status_label.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {TEXT_DIM}; background: transparent;"
        )

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.status_label)

    def set_ready(self, ready):

        if ready:
            self.status_label.setText("✔  Pronto")
            self.status_label.setStyleSheet(
                f"font-size: 12px; font-weight: 700; color: {SUCCESS}; background: transparent;"
            )
        else:
            self.status_label.setText("✕  Não pronto")
            self.status_label.setStyleSheet(
                f"font-size: 12px; font-weight: 700; color: {WARNING}; background: transparent;"
            )


class ReadinessPage(QWidget):
    """Prontidão para inspeção periódica / emissões — o mesmo tipo de
    verificação que o OBD Auto Doctor e outras ferramentas profissionais
    mostram antes de uma inspeção obrigatória."""

    def __init__(self):

        super().__init__()

        self.protocol = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header(
            "Prontidão para Inspeção",
            "Verifica se os sistemas de emissões já completaram os testes "
            "internos — útil antes de uma inspeção periódica obrigatória."
        ))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.check_button = QPushButton("🛡   Verificar Prontidão")
        self.check_button.setObjectName("primaryButton")
        self.check_button.setMinimumHeight(38)
        self.check_button.setCursor(Qt.PointingHandCursor)
        self.check_button.clicked.connect(self.check_readiness)
        toolbar.addWidget(self.check_button)
        toolbar.addStretch()
        content_layout.addLayout(toolbar)

        self.summary_card = self.build_summary_card()
        content_layout.addWidget(self.summary_card)

        self.grid_wrapper = QWidget()
        self.grid = QGridLayout(self.grid_wrapper)
        self.grid.setSpacing(10)
        content_layout.addWidget(self.grid_wrapper)

        self.hint = empty_hint(
            "Sem verificação feita ainda. Clica em \"Verificar Prontidão\"."
        )
        content_layout.addWidget(self.hint)

        content_layout.addStretch()

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para verificares a prontidão para inspeção."
        )
        layout.addWidget(self.stack, 1)

        self.set_protocol(None)

    def build_summary_card(self):

        card = QFrame()
        card.setObjectName("summaryCard")
        card.setStyleSheet(f"""
        #summaryCard {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(28)

        self.mil_label = self._summary_item("Luz de avaria (MIL)")
        self.dtc_label = self._summary_item("Códigos ativos")
        self.ignition_label = self._summary_item("Tipo de motor")

        layout.addWidget(self.mil_label[0])
        layout.addWidget(self.dtc_label[0])
        layout.addWidget(self.ignition_label[0])
        layout.addStretch()

        return card

    def _summary_item(self, title):

        wrapper = QWidget()
        inner = QVBoxLayout(wrapper)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(2)

        name = QLabel(title.upper())
        name.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {TEXT_DIM}; "
            f"letter-spacing: 1px; background: transparent;"
        )

        value = QLabel("—")
        value.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {TEXT}; background: transparent;"
        )

        inner.addWidget(name)
        inner.addWidget(value)

        return wrapper, value

    def set_protocol(self, protocol):

        self.protocol = protocol
        self.check_button.setEnabled(protocol is not None)
        self.stack.setCurrentIndex(1 if protocol is not None else 0)

        if not protocol:
            self._clear_grid()

    def check_readiness(self):

        if not self.protocol:
            return

        try:
            data = self.protocol.readiness()
        except Exception as error:
            QMessageBox.warning(
                self, "Erro", f"Não foi possível ler a prontidão:\n{error}"
            )
            return

        if not data:
            QMessageBox.information(
                self, "Sem resposta",
                "O veículo não respondeu ao pedido de prontidão (PID 01)."
            )
            return

        self.mil_label[1].setText("Acesa" if data["mil_on"] else "Apagada")
        self.mil_label[1].setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: "
            f"{DANGER if data['mil_on'] else SUCCESS}; background: transparent;"
        )

        self.dtc_label[1].setText(str(data["dtc_count"]))
        self.ignition_label[1].setText(data["ignition_type"])

        self._clear_grid()

        for index, monitor in enumerate(data["monitors"]):

            tile = MonitorTile(monitor["name"])
            tile.set_ready(monitor["ready"])

            self.grid.addWidget(tile, index // 2, index % 2)

    def _clear_grid(self):

        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
