from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QGridLayout
)

from gui.widgets import page_header, empty_hint, page_with_gate
from gui.styles import CARD_BG, CARD_BORDER, TEXT, TEXT_DIM, TEXT_FAINT


class InfoTile(QFrame):

    def __init__(self, label, value="—"):

        super().__init__()

        self.setObjectName("infoTile")
        self.setStyleSheet(f"""
        #infoTile {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 10px;
        }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        name = QLabel(label.upper())
        name.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {TEXT_DIM}; "
            f"letter-spacing: 1px; background: transparent;"
        )

        self.value_label = QLabel(value)
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {TEXT}; "
            f"background: transparent;"
        )

        layout.addWidget(name)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(value or "—")


class ModulesPage(QWidget):
    """
    Nota honesta sobre o que aqui é mostrado: em OBD-II genérico (sem um
    protocolo de fabricante como UDS/KWP com endereços proprietários),
    não existe uma forma standard de listar cada centralina (ABS,
    Airbag, Caixa...) individualmente — isso é o que ferramentas como o
    VCDS fazem com bases de dados específicas da VAG. Aqui mostramos a
    informação real e fiável que a norma garante: dados da passarela
    (gateway) de diagnóstico e, sempre que o veículo o suportar, o nome
    da ECU que respondeu.
    """

    def __init__(self):

        super().__init__()

        self.protocol = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header(
            "Módulos de Controlo",
            "Informação da passarela de diagnóstico OBD-II do veículo."
        ))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.tile_protocol = InfoTile("Protocolo de comunicação")
        self.tile_vin = InfoTile("VIN")
        self.tile_ecu = InfoTile("Nome da ECU (se disponível)")
        self.tile_pids = InfoTile("PIDs suportados (Modo 01)")

        grid.addWidget(self.tile_protocol, 0, 0)
        grid.addWidget(self.tile_vin, 0, 1)
        grid.addWidget(self.tile_ecu, 1, 0)
        grid.addWidget(self.tile_pids, 1, 1)

        content_layout.addLayout(grid)

        content_layout.addWidget(empty_hint(
            "Para leitura de módulos individuais (ABS, Airbag, Caixa...) "
            "com endereçamento de fabricante — como no VCDS — é preciso "
            "um protocolo proprietário (UDS/KWP) por marca. Os Códigos "
            "de Falha nesta app já são separados por sistema (Motor, "
            "Travagem/ABS, Carroçaria/Airbag, Rede) sempre que a "
            "centralina reporta essa informação via OBD-II."
        ))

        content_layout.addStretch()

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para veres a informação da passarela "
            "de diagnóstico."
        )
        layout.addWidget(self.stack, 1)

    def set_protocol(self, protocol, vehicle_info=None):

        self.protocol = protocol

        self.stack.setCurrentIndex(1 if protocol else 0)

        if not protocol:
            self.tile_protocol.set_value("—")
            self.tile_vin.set_value("—")
            self.tile_ecu.set_value("—")
            self.tile_pids.set_value("—")
            return

        vehicle_info = vehicle_info or {}

        self.tile_protocol.set_value(vehicle_info.get("protocol_name"))
        self.tile_vin.set_value(vehicle_info.get("vin"))
        self.tile_ecu.set_value(vehicle_info.get("ecu_name"))

        pid_count = vehicle_info.get("supported_pid_count")
        self.tile_pids.set_value(str(pid_count) if pid_count is not None else "—")
