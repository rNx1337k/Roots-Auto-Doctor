from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame
)

from hardware.serial_interface import SerialInterface
from hardware.elm327 import ELM327
from services.connection_manager import ConnectionManager
from services.vin_lookup import guess_make
from protocols.obd2 import OBD2
from core.vehicle import Vehicle
from app.logger import Logger
from app.config import DEFAULT_OBD_BAUDRATE, SERIAL_TIMEOUT
from gui.widgets import StatusPill, page_header, empty_hint
from gui.styles import CARD_BG, CARD_BORDER, TEXT_DIM, SUCCESS, WARNING, DANGER


class IdentifyWorker(QThread):
    """Faz a inicialização do ELM327 e a identificação do veículo
    (protocolo, VIN, PIDs suportados) fora da thread da interface,
    para a app nunca 'congelar' enquanto o adaptador responde."""

    finished_ok = Signal(object, dict)
    failed = Signal(str)

    def __init__(self, interface, logger):

        super().__init__()

        self.interface = interface
        self.logger = logger

    def run(self):

        try:
            elm = ELM327(self.interface, logger=self.logger)
            elm.initialize()

            protocol_name = None
            try:
                protocol_name = elm.detect_protocol()
            except Exception:
                pass

            obd2 = OBD2(elm)

            vin = None
            ecu_name = None
            supported = set()

            try:
                vin = obd2.vin()
            except Exception:
                pass

            try:
                ecu_name = obd2.ecu_name()
            except Exception:
                pass

            try:
                supported = obd2.supported_pids()
            except Exception:
                pass

            voltage = None
            try:
                voltage = elm.battery_voltage()
            except Exception:
                pass

            info = {
                "protocol_name": protocol_name,
                "vin": vin,
                "ecu_name": ecu_name,
                "supported_pid_count": len(supported),
                "supported_pids": supported,
                "battery_voltage": voltage,
            }

        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished_ok.emit(obd2, info)


class ConnectionPage(QWidget):

    # (estado, mensagem) -> "connected" | "connecting" | "disconnected" | "error"
    connectionChanged = Signal(str, str)

    # (protocolo OBD2 ou None, informação do veículo dict)
    protocolReady = Signal(object, dict)

    # linha de comunicação (AT/OBD), para a página de Registo
    logLine = Signal(str)

    def __init__(self):

        super().__init__()

        self.manager = ConnectionManager()
        self.logger = Logger(on_message=self._on_log_line)
        self.identify_worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(page_header(
            "Ligação",
            "Seleciona a porta da tua interface de diagnóstico "
            "(ELM327, cabo KKL, J2534) e liga-te ao veículo."
        ))

        layout.addWidget(self.build_card())
        layout.addWidget(empty_hint(
            "Dica: com o motor desligado e a chave na posição \"Ignição\", "
            "muitas centralinas já respondem a pedidos de diagnóstico."
        ))
        layout.addStretch()

        self.refresh_ports()

    def build_card(self):

        card = QFrame()
        card.setObjectName("card")

        card.setStyleSheet(f"""
        #card {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        label = QLabel("INTERFACE DE DIAGNÓSTICO")
        label.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {TEXT_DIM}; "
            f"letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(label)

        port_row = QHBoxLayout()
        port_row.setSpacing(10)

        self.ports = QComboBox()
        self.ports.setMinimumHeight(38)
        port_row.addWidget(self.ports, 1)

        refresh = QPushButton("⟳   Atualizar")
        refresh.setMinimumHeight(38)
        refresh.setCursor(Qt.PointingHandCursor)
        refresh.clicked.connect(self.refresh_ports)
        port_row.addWidget(refresh)

        layout.addLayout(port_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.connect_button = QPushButton("Ligar")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.setMinimumHeight(40)
        self.connect_button.setMinimumWidth(140)
        self.connect_button.setCursor(Qt.PointingHandCursor)
        self.connect_button.clicked.connect(self.toggle_connection)
        action_row.addWidget(self.connect_button)

        self.status_pill = StatusPill("disconnected")
        action_row.addWidget(self.status_pill)

        self.voltage_label = QLabel("")
        self.voltage_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; font-weight: 600; "
            f"background: transparent;"
        )
        action_row.addWidget(self.voltage_label)

        action_row.addStretch()

        layout.addLayout(action_row)

        self.status = QLabel("Sem ligação estabelecida.")
        self.status.setWordWrap(True)
        self.status.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self.status)

        return card

    def refresh_ports(self):

        self.ports.clear()

        ports = SerialInterface.ports()

        if not ports:
            self.ports.addItem("Nenhuma porta encontrada", None)
            return

        for port in ports:
            self.ports.addItem(
                f"{port['device']}  —  {port['description']}",
                port["device"]
            )

    def toggle_connection(self):

        if self.manager.connected():
            self.disconnect()
        else:
            self.connect()

    def connect(self):

        device = self.ports.currentData()

        if not device:
            self.set_status("error", "Seleciona uma porta válida.")
            return

        self.connect_button.setEnabled(False)
        self.set_status("connecting", "A ligar ao adaptador...")

        try:
            interface = SerialInterface(
                device,
                baudrate=DEFAULT_OBD_BAUDRATE,
                timeout=SERIAL_TIMEOUT
            )
            self.manager.set_interface(interface)
            self.manager.connect()

        except Exception as error:
            self.set_status("error", f"Falha na ligação: {error}")
            self.connect_button.setEnabled(True)
            return

        self.set_status("connecting", "A identificar o veículo...")

        self.identify_worker = IdentifyWorker(interface, self.logger)
        self.identify_worker.finished_ok.connect(self.on_identified)
        self.identify_worker.failed.connect(self.on_identify_failed)
        self.identify_worker.start()

    def on_identified(self, obd2, info):

        self.connect_button.setEnabled(True)
        self.connect_button.setText("Desligar")

        device = self.ports.currentData()
        message = f"Ligado via {device} — {info.get('protocol_name') or 'protocolo automático'}."
        self.set_status("connected", message)
        self.set_voltage(info.get("battery_voltage"))

        vehicle = Vehicle()
        vehicle.connected = True
        vehicle.vin = info.get("vin")
        vehicle.protocol = info.get("protocol_name")
        vehicle.make = guess_make(info.get("vin")) if info.get("vin") else None
        vehicle.battery_voltage = info.get("battery_voltage")

        info["vehicle"] = vehicle
        info["label"] = f"{vehicle.make or ''}".strip() or None

        self.protocolReady.emit(obd2, info)

    def on_identify_failed(self, message):

        self.connect_button.setEnabled(True)
        self.connect_button.setText("Desligar")
        self.set_status(
            "connected",
            f"Ligado ao adaptador, mas a identificação do veículo "
            f"falhou: {message}\nConfirma que a chave está na "
            f"posição \"Ignição\" e que a ficha OBD-II está bem "
            f"encaixada, depois tenta ler os Códigos de Falha na "
            f"mesma — pode funcionar mesmo assim."
        )
        self.set_voltage(None)
        self.protocolReady.emit(None, {})

    def disconnect(self):

        if self.identify_worker and self.identify_worker.isRunning():
            self.identify_worker.terminate()
            self.identify_worker.wait(500)

        self.manager.disconnect()

        self.connect_button.setText("Ligar")
        self.set_status("disconnected", "Sem ligação estabelecida.")
        self.set_voltage(None)
        self.protocolReady.emit(None, {})

    def set_voltage(self, voltage):

        if voltage is None:
            self.voltage_label.setText("")
            return

        if voltage < 11.5:
            color = DANGER
        elif voltage > 15.0:
            color = WARNING
        else:
            color = SUCCESS

        self.voltage_label.setText(f"🔋  {voltage:g}V")
        self.voltage_label.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 700; "
            f"background: transparent;"
        )

    def set_status(self, state, message):

        self.status_pill.set_state(state)
        self.status.setText(message)

        self.connectionChanged.emit(state, message)

    def _on_log_line(self, line):
        self.logLine.emit(line)
