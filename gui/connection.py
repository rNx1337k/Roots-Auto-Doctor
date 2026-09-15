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
from app.config import DEFAULT_OBD_BAUDRATE, SERIAL_TIMEOUT, BAUD_CANDIDATES
from gui.widgets import StatusPill, page_header, empty_hint
from gui.styles import (
    CARD_BG, CARD_BORDER, TEXT_DIM, SUCCESS, WARNING, DANGER, get_settings
)

LAST_PORT_SETTINGS_KEY = "connection/last_port"
LAST_BAUD_SETTINGS_KEY = "connection/last_baud"


class IdentifyWorker(QThread):
    """Inicializa o ELM327 e identifica o veículo fora da UI."""

    finished_ok = Signal(object, dict)
    failed = Signal(str)
    status = Signal(str)

    def __init__(self, interface, logger, baudrate):
        super().__init__()
        self.interface = interface
        self.logger = logger
        self.baudrate = baudrate
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            if self._cancel:
                return

            baud = self._negotiate_baud()
            if self._cancel:
                return

            self.status.emit(f"Adaptador a {baud} baud — a inicializar...")

            elm = ELM327(self.interface, logger=self.logger)
            elm.initialize()

            if self._cancel:
                return

            protocol_name = None
            try:
                protocol_name = elm.detect_protocol()
            except Exception:
                pass

            obd2 = OBD2(elm)

            vin = None
            ecu_name = None
            supported = set()
            voltage = None

            self.status.emit("A ler VIN e PIDs suportados...")

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

            try:
                voltage = elm.battery_voltage()
            except Exception:
                pass

            if self._cancel:
                return

            info = {
                "protocol_name": protocol_name,
                "vin": vin,
                "ecu_name": ecu_name,
                "supported_pid_count": len(supported),
                "supported_pids": supported,
                "battery_voltage": voltage,
                "baudrate": baud,
                "is_can": bool(getattr(elm, "is_can", False)),
            }

        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished_ok.emit(obd2, info)

    def _negotiate_baud(self):
        if self.baudrate:
            self.interface.set_baudrate(self.baudrate)
            return self.baudrate

        last_error = None
        for baud in BAUD_CANDIDATES:
            if self._cancel:
                break
            try:
                self.status.emit(f"A testar {baud} baud...")
                self.interface.set_baudrate(baud)
                elm = ELM327(self.interface, logger=self.logger)
                if elm.probe():
                    return baud
            except Exception as error:
                last_error = error
                continue

        if last_error:
            raise last_error
        return DEFAULT_OBD_BAUDRATE


class ConnectionPage(QWidget):

    connectionChanged = Signal(str, str)
    protocolReady = Signal(object, dict)
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

        self.baud = QComboBox()
        self.baud.setMinimumHeight(38)
        self.baud.setMinimumWidth(130)
        self.baud.setToolTip(
            "Velocidade série. \"Auto\" testa 38400, 115200, 9600 e 57600."
        )
        self.baud.addItem("Auto", None)
        for rate in BAUD_CANDIDATES:
            self.baud.addItem(str(rate), rate)
        port_row.addWidget(self.baud)

        refresh = QPushButton("Atualizar")
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

        last_baud = get_settings().value(LAST_BAUD_SETTINGS_KEY, None)
        if last_baud:
            try:
                last_baud = int(last_baud)
            except (TypeError, ValueError):
                last_baud = None
            idx = self.baud.findData(last_baud)
            if idx >= 0:
                self.baud.setCurrentIndex(idx)

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

        last_port = get_settings().value(LAST_PORT_SETTINGS_KEY, None)
        if last_port:
            index = self.ports.findData(last_port)
            if index >= 0:
                self.ports.setCurrentIndex(index)

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

        baud = self.baud.currentData()
        initial_baud = baud or DEFAULT_OBD_BAUDRATE

        try:
            interface = SerialInterface(
                device,
                baudrate=initial_baud,
                timeout=SERIAL_TIMEOUT
            )
            self.manager.set_interface(interface)
            self.manager.connect()
        except Exception as error:
            self.set_status("error", f"Falha na ligação: {error}")
            self.connect_button.setEnabled(True)
            return

        self.set_status("connecting", "A identificar o veículo...")

        self.identify_worker = IdentifyWorker(interface, self.logger, baud)
        self.identify_worker.finished_ok.connect(self.on_identified)
        self.identify_worker.failed.connect(self.on_identify_failed)
        self.identify_worker.status.connect(
            lambda msg: self.set_status("connecting", msg)
        )
        self.identify_worker.start()

    def on_identified(self, obd2, info):
        self.connect_button.setEnabled(True)
        self.connect_button.setText("Desligar")

        device = self.ports.currentData()
        settings = get_settings()
        settings.setValue(LAST_PORT_SETTINGS_KEY, device)
        if info.get("baudrate"):
            settings.setValue(LAST_BAUD_SETTINGS_KEY, int(info["baudrate"]))
        settings.sync()

        baud_txt = f" @ {info.get('baudrate')} baud" if info.get("baudrate") else ""
        message = (
            f"Ligado via {device}{baud_txt} — "
            f"{info.get('protocol_name') or 'protocolo automático'}."
        )
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
        self.connect_button.setText("Ligar")
        self.manager.disconnect()
        self.set_status(
            "error",
            f"Não foi possível identificar o veículo: {message}\n"
            "Confirma a porta, a velocidade (tenta Auto) e que a chave "
            "está na posição \"Ignição\"."
        )
        self.set_voltage(None)
        self.protocolReady.emit(None, {})

    def disconnect(self):
        worker = self.identify_worker

        if worker and worker.isRunning():
            worker.cancel()
            # Fechar a porta força leituras seriais pendentes a terminar.
            self.manager.disconnect()

            if worker.wait(5000):
                self.identify_worker = None
        else:
            self.manager.disconnect()
            self.identify_worker = None

        self.connect_button.setEnabled(True)
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

        self.voltage_label.setText(f"Bateria  {voltage:g} V")
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
