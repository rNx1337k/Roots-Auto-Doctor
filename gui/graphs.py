from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton
)

from gui.widgets import page_header, empty_hint, LiveGraph, page_with_gate
from services.pid_database import get_pid
from app.config import LIVE_DATA_INTERVAL

# Painel fixo com os sensores mais úteis para acompanhar de relance
# durante um teste de estrada — motor, velocidade, temperatura e carga.
OVERVIEW_PIDS = [0x0C, 0x0D, 0x05, 0x11]


class OverviewWorker(QThread):
    """Lê em ciclo contínuo os PIDs do painel de visão geral, num
    thread próprio, para não bloquear a interface."""

    sample = Signal(int, object, str)
    error = Signal(str)

    def __init__(self, protocol, pids, interval=LIVE_DATA_INTERVAL):

        super().__init__()

        self.protocol = protocol
        self.pids = pids
        self.interval = interval
        self._running = True

    def run(self):

        while self._running:

            for pid in self.pids:

                if not self._running:
                    break

                try:
                    value, unit = self.protocol.read_pid(pid)
                except Exception as error:
                    self.error.emit(str(error))
                    continue

                self.sample.emit(pid, value, unit or "")

            self.msleep(int(self.interval * 1000))

    def stop(self):
        self._running = False


class GraphsPage(QWidget):
    """Painel com vários parâmetros ao vivo lado a lado — útil para um
    teste de estrada, sem teres de andar a trocar de parâmetro como na
    página 'Dados em Tempo Real'."""

    def __init__(self):

        super().__init__()

        self.protocol = None
        self.worker = None
        self.graphs_by_pid = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header(
            "Gráficos",
            "Painel com os parâmetros mais úteis para um teste de "
            "estrada, todos a atualizar ao mesmo tempo."
        ))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        toolbar = QHBoxLayout()

        self.start_button = QPushButton("▶   Iniciar Monitorização")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(38)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_stream)

        self.stop_button = QPushButton("⏸   Parar")
        self.stop_button.setMinimumHeight(38)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_stream)

        toolbar.addWidget(self.start_button)
        toolbar.addWidget(self.stop_button)
        toolbar.addStretch()

        content_layout.addLayout(toolbar)

        grid = QGridLayout()
        grid.setSpacing(14)

        for index, pid in enumerate(OVERVIEW_PIDS):

            entry = get_pid(pid)

            if not entry:
                continue

            graph = LiveGraph(
                title=entry["name"], unit=entry["unit"]
            )
            graph.set_series(
                entry["name"], entry["unit"], entry["min"], entry["max"]
            )

            self.graphs_by_pid[pid] = graph
            grid.addWidget(graph, index // 2, index % 2)

        content_layout.addLayout(grid, 1)

        content_layout.addWidget(empty_hint(
            "Para acompanhares qualquer outro parâmetro (fuel trim, "
            "sondas lambda, etc.), usa \"Dados em Tempo Real\" e clica "
            "no ícone 📈 na respetiva linha."
        ))

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para veres os gráficos ao vivo."
        )
        layout.addWidget(self.stack, 1)

        self.set_protocol(None)

    # ------------------------------------------------------------------

    def set_protocol(self, protocol):

        self.stop_stream()
        self.protocol = protocol
        self.start_button.setEnabled(protocol is not None)
        self.stack.setCurrentIndex(1 if protocol is not None else 0)

    def start_stream(self):

        if not self.protocol:
            return

        for graph in self.graphs_by_pid.values():
            graph.clear_series()

        self.worker = OverviewWorker(self.protocol, OVERVIEW_PIDS)
        self.worker.sample.connect(self.on_sample)
        self.worker.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_stream(self):

        if self.worker:
            self.worker.stop()
            self.worker.wait(1500)
            self.worker = None

        self.start_button.setEnabled(self.protocol is not None)
        self.stop_button.setEnabled(False)

    def on_sample(self, pid, value, _unit):

        graph = self.graphs_by_pid.get(pid)

        if graph and isinstance(value, (int, float)):
            graph.add_value(value)
