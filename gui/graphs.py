from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton
)
import time

from gui.widgets import page_header, empty_hint, LiveGraph, page_with_gate
from services.pid_database import get_pid
from services.units import convert_for_display, convert_range
from app.config import LIVE_DATA_INTERVAL

# Painel fixo com os sensores mais úteis para acompanhar de relance
# durante um teste de estrada — motor, velocidade, temperatura e carga.
OVERVIEW_PIDS = [0x0C, 0x0D, 0x05, 0x11]


class OverviewWorker(QThread):
    """Lê em ciclo contínuo os PIDs do painel de visão geral, num
    thread próprio, para não bloquear a interface.

    Usa o mesmo rate-limiting adaptativo do LiveDataWorker: só dorme
    o tempo que falta para atingir o intervalo alvo."""

    sample = Signal(int, object, str)
    error = Signal(str)

    def __init__(self, protocol, pids, interval=LIVE_DATA_INTERVAL):
        super().__init__()
        self.protocol = protocol
        self.pids = list(pids)
        self.interval = max(0.02, float(interval))
        self._running = True

    def run(self):
        adapter = getattr(self.protocol, "adapter", None)
        if adapter is not None and hasattr(adapter, "set_fast_mode"):
            try:
                adapter.set_fast_mode(True)
            except Exception:
                pass

        try:
            while self._running:
                t0 = time.monotonic()

                try:
                    if hasattr(self.protocol, "read_pids"):
                        values = self.protocol.read_pids(self.pids)
                    else:
                        values = {
                            pid: self.protocol.read_pid(pid)
                            for pid in self.pids
                        }
                except Exception as error:
                    self.error.emit(str(error))
                    self.msleep(200)
                    continue

                for pid, pair in values.items():
                    if not self._running:
                        break
                    value, unit = pair if pair else (None, "")
                    self.sample.emit(pid, value, unit or "")

                elapsed = time.monotonic() - t0
                remaining_ms = int((self.interval - elapsed) * 1000)
                if remaining_ms > 2:
                    self.msleep(remaining_ms)
        finally:
            if adapter is not None and hasattr(adapter, "set_fast_mode"):
                try:
                    adapter.set_fast_mode(False)
                except Exception:
                    pass

    def stop(self):
        self._running = False


class GraphsPage(QWidget):
    """Painel com vários parâmetros ao vivo lado a lado — útil para um
    teste de estrada, sem teres de andar a trocar de parâmetro como na
    página 'Dados em Tempo Real'."""

    streamStarted = Signal()

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

            min_v, max_v, unit = convert_range(entry["min"], entry["max"], entry["unit"])
            graph.set_series(entry["name"], unit, min_v, max_v)

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

        self.streamStarted.emit()

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
            self.worker.wait(2000)
            self.worker = None

        self.start_button.setEnabled(self.protocol is not None)
        self.stop_button.setEnabled(False)

    def on_sample(self, pid, value, unit):

        value, _unit = convert_for_display(value, unit)

        graph = self.graphs_by_pid.get(pid)

        if graph and isinstance(value, (int, float)):
            graph.add_value(value)
