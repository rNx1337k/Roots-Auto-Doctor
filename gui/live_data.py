from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSplitter,
    QStackedWidget,
    QScrollArea,
    QFileDialog,
    QMessageBox
)
from datetime import datetime
import time

from gui.widgets import page_header, empty_hint, LiveGraph, Gauge, page_with_gate
from gui.styles import TEXT_FAINT
from services.pid_database import PID_TABLE, ALL_CATEGORIES, get_pid
from services.session_export import export_live_data_csv
from services.units import preferred_unit, convert_for_display, convert_range
from app.config import (
    LIVE_DATA_INTERVAL,
    LIVE_DATA_PRESETS,
    LIVE_DATA_DEFAULT_PRESET,
    DEFAULT_LIVE_PIDS,
)


class LiveDataWorker(QThread):
    sample = Signal(int, object, str)
    error = Signal(str)
    cycle_done = Signal(float)
    streamStarted = Signal()

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
                pids = list(self.pids)
                if not pids:
                    self.msleep(80)
                    continue

                try:
                    if hasattr(self.protocol, "read_pids"):
                        values = self.protocol.read_pids(pids)
                    else:
                        values = {
                            pid: self.protocol.read_pid(pid) for pid in pids
                        }
                except Exception as error:
                    self.error.emit(str(error))
                    self.msleep(200)
                    continue

                if not self._running:
                    break

                for pid, pair in values.items():
                    if not self._running:
                        break
                    value, unit = pair if pair else (None, "")
                    self.sample.emit(pid, value, unit or "")

                elapsed = time.monotonic() - t0
                self.cycle_done.emit(elapsed)
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


class LiveDataPage(QWidget):

    streamStarted = Signal()

    def __init__(self):
        super().__init__()

        self.protocol = None
        self.worker = None
        self.selected_pids = set()
        self.supported_pids = None
        self.rows_by_pid = {}
        self.graphed_pid = None
        self.gauges_by_pid = {}
        self.view_mode = "table"
        self.recording = False
        self.recorded_samples = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(page_header(
            "Dados em Tempo Real",
            "Escolhe os parâmetros (PIDs) que queres transmitir ao vivo "
            "e acompanha os valores numa tabela e num gráfico."
        ))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        content_layout.addLayout(self.build_toolbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.build_left_panel())
        splitter.addWidget(self.build_graph_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        content_layout.addWidget(splitter, 1)

        content_layout.addWidget(empty_hint(
            "Marca um ou mais parâmetros na tabela e clica em "
            "\"Iniciar Leitura\". Em CAN vários PIDs são pedidos no mesmo "
            "ciclo para máxima taxa de actualização."
        ))

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para transmitires parâmetros em tempo real."
        )
        layout.addWidget(self.stack, 1)

        self.set_protocol(None)

    def build_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar parâmetro...")
        self.search.setMinimumHeight(36)
        self.search.setMaximumWidth(220)
        self.search.textChanged.connect(self.populate_table)

        self.category = QComboBox()
        self.category.addItem("Todas")
        for cat in ALL_CATEGORIES:
            self.category.addItem(cat)
        self.category.setMinimumHeight(36)
        self.category.currentTextChanged.connect(self.populate_table)

        self.supported_only = QCheckBox("Só suportados")
        self.supported_only.setChecked(True)
        self.supported_only.setToolTip(
            "Esconde PIDs que a ECU não anunciou no bitmask de suporte."
        )
        self.supported_only.toggled.connect(self.populate_table)

        self.rate_combo = QComboBox()
        self.rate_combo.setMinimumHeight(36)
        self.rate_combo.setMinimumWidth(110)
        self.rate_combo.setToolTip(
            "Taxa alvo de atualização. Com muitos PIDs o tempo de "
            "comunicação com a ECU limita a taxa real."
        )
        for label in LIVE_DATA_PRESETS:
            self.rate_combo.addItem(label)
        default_idx = list(LIVE_DATA_PRESETS.keys()).index(
            LIVE_DATA_DEFAULT_PRESET
        ) if LIVE_DATA_DEFAULT_PRESET in LIVE_DATA_PRESETS else 0
        self.rate_combo.setCurrentIndex(default_idx)

        self.rate_label = QLabel("")
        self.rate_label.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 11px;")
        self.rate_label.setMinimumWidth(70)

        self.start_button = QPushButton("▶   Iniciar Leitura")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(38)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_stream)

        self.stop_button = QPushButton("⏸   Parar")
        self.stop_button.setMinimumHeight(38)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_stream)

        self.record_button = QPushButton("⏺   Gravar")
        self.record_button.setCheckable(True)
        self.record_button.setMinimumHeight(38)
        self.record_button.setCursor(Qt.PointingHandCursor)
        self.record_button.setToolTip(
            "Regista os valores lidos para depois exportares para CSV."
        )
        self.record_button.clicked.connect(self.toggle_recording)

        self.export_live_button = QPushButton("⬇   Exportar CSV")
        self.export_live_button.setMinimumHeight(38)
        self.export_live_button.setCursor(Qt.PointingHandCursor)
        self.export_live_button.setEnabled(False)
        self.export_live_button.clicked.connect(self.export_recording)

        self.table_view_button = QPushButton("☰  Tabela")
        self.table_view_button.setCheckable(True)
        self.table_view_button.setChecked(True)
        self.table_view_button.setMinimumHeight(36)
        self.table_view_button.setCursor(Qt.PointingHandCursor)
        self.table_view_button.clicked.connect(lambda: self.set_view_mode("table"))

        self.gauge_view_button = QPushButton("◎  Mostradores")
        self.gauge_view_button.setCheckable(True)
        self.gauge_view_button.setMinimumHeight(36)
        self.gauge_view_button.setCursor(Qt.PointingHandCursor)
        self.gauge_view_button.clicked.connect(lambda: self.set_view_mode("gauges"))

        toolbar.addWidget(self.search)
        toolbar.addWidget(self.category)
        toolbar.addWidget(self.supported_only)
        toolbar.addWidget(self.table_view_button)
        toolbar.addWidget(self.gauge_view_button)
        toolbar.addStretch()
        toolbar.addWidget(self.rate_combo)
        toolbar.addWidget(self.rate_label)
        toolbar.addWidget(self.record_button)
        toolbar.addWidget(self.export_live_button)
        toolbar.addWidget(self.start_button)
        toolbar.addWidget(self.stop_button)

        return toolbar

    def build_table(self):
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "", "Parâmetro", "Valor", "Unidade", "Gráfico"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(0, 34)
        self.table.setColumnWidth(4, 70)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.populate_table()
        return self.table

    def build_left_panel(self):
        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(self.build_table())
        self.left_stack.addWidget(self.build_gauges_panel())
        return self.left_stack

    def build_gauges_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.gauges_grid = QGridLayout(container)
        self.gauges_grid.setSpacing(12)
        scroll.setWidget(container)

        self.gauges_hint = QLabel(
            "Marca parâmetros na tabela e inicia a leitura para "
            "veres os mostradores aqui."
        )
        self.gauges_hint.setWordWrap(True)
        self.gauges_hint.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px;")
        self.gauges_grid.addWidget(self.gauges_hint, 0, 0)
        return scroll

    def set_view_mode(self, mode):
        self.view_mode = mode
        self.table_view_button.setChecked(mode == "table")
        self.gauge_view_button.setChecked(mode == "gauges")
        self.left_stack.setCurrentIndex(0 if mode == "table" else 1)
        if mode == "gauges":
            self.refresh_gauges()

    def refresh_gauges(self):
        while self.gauges_grid.count():
            item = self.gauges_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.gauges_by_pid = {}
        pids = sorted(self.selected_pids)

        if not pids:
            hint = QLabel(
                "Marca parâmetros na tabela e inicia a leitura para "
                "veres os mostradores aqui."
            )
            hint.setWordWrap(True)
            hint.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px;")
            self.gauges_grid.addWidget(hint, 0, 0)
            return

        for index, pid in enumerate(pids):
            entry = get_pid(pid)
            if not entry:
                continue
            min_v, max_v, unit = convert_range(entry["min"], entry["max"], entry["unit"])
            gauge = Gauge(entry["name"], unit, min_v, max_v)
            self.gauges_by_pid[pid] = gauge
            self.gauges_grid.addWidget(gauge, index // 3, index % 3)

    def build_graph_panel(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.graph = LiveGraph(title="Seleciona um parâmetro", unit="")
        layout.addWidget(self.graph)
        layout.addStretch()
        return wrapper

    def populate_table(self):
        term = self.search.text().strip().lower()
        category = self.category.currentText()
        only_supported = self.supported_only.isChecked()

        self.table.setRowCount(0)
        self.rows_by_pid = {}

        for entry in PID_TABLE:
            if category != "Todas" and entry["category"] != category:
                continue
            if term and term not in entry["name"].lower():
                continue
            if (
                only_supported
                and self.supported_pids is not None
                and entry["pid"] not in self.supported_pids
            ):
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            checkbox = QCheckBox()
            checkbox.setChecked(entry["pid"] in self.selected_pids)
            checkbox.stateChanged.connect(
                lambda state, pid=entry["pid"]: self.toggle_pid(pid, state)
            )

            cell = QWidget()
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.addWidget(checkbox)

            name_item = QTableWidgetItem(entry["name"])
            if (
                self.supported_pids is not None
                and entry["pid"] not in self.supported_pids
            ):
                name_item.setForeground(Qt.gray)

            self.table.setCellWidget(row, 0, cell)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, QTableWidgetItem("—"))
            self.table.setItem(row, 3, QTableWidgetItem(preferred_unit(entry["unit"])))

            graph_button = QPushButton("📈")
            graph_button.setCursor(Qt.PointingHandCursor)
            graph_button.setFixedWidth(50)
            graph_button.clicked.connect(
                lambda _checked, pid=entry["pid"]: self.show_in_graph(pid)
            )
            self.table.setCellWidget(row, 4, graph_button)
            self.rows_by_pid[entry["pid"]] = row

    def set_protocol(self, protocol, vehicle_info=None):
        self.stop_stream()
        self.protocol = protocol
        vehicle_info = vehicle_info or {}
        supported = vehicle_info.get("supported_pids")
        self.supported_pids = set(supported) if supported else None

        self.start_button.setEnabled(protocol is not None)
        self.stack.setCurrentIndex(1 if protocol is not None else 0)

        if protocol is None:
            self.record_button.setChecked(False)
            self.recording = False
            self.record_button.setText("⏺   Gravar")
            self.selected_pids = set()
        elif not self.selected_pids:
            defaults = [
                pid for pid in DEFAULT_LIVE_PIDS
                if self.supported_pids is None or pid in self.supported_pids
            ]
            self.selected_pids = set(defaults)

        self.populate_table()

    def toggle_pid(self, pid, state):
        if state:
            self.selected_pids.add(pid)
        else:
            self.selected_pids.discard(pid)

        if self.worker and self.worker.isRunning():
            self.worker.pids = list(self.selected_pids)

    def show_in_graph(self, pid):
        entry = get_pid(pid)
        if not entry:
            return
        self.graphed_pid = pid
        min_v, max_v, unit = convert_range(entry["min"], entry["max"], entry["unit"])
        self.graph.set_series(entry["name"], unit, min_v, max_v)

    def start_stream(self):
        if not self.protocol:
            return
        if not self.selected_pids:
            QMessageBox.information(
                self, "Sem parâmetros",
                "Marca pelo menos um parâmetro na tabela antes de iniciar."
            )
            return

        self.streamStarted.emit()

        preset = self.rate_combo.currentText()
        interval = LIVE_DATA_PRESETS.get(preset, LIVE_DATA_INTERVAL)

        self.worker = LiveDataWorker(
            self.protocol,
            list(self.selected_pids),
            interval=interval,
        )
        self.worker.sample.connect(self.on_sample)
        self.worker.cycle_done.connect(self.on_cycle_done)
        self.worker.start()

        self.refresh_gauges()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.rate_combo.setEnabled(False)
        self.rate_label.setText("…")

    def stop_stream(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2500)
            self.worker = None

        self.start_button.setEnabled(
            self.protocol is not None and bool(self.selected_pids)
        )
        self.stop_button.setEnabled(False)
        self.rate_combo.setEnabled(True)
        self.rate_label.setText("")

    def on_cycle_done(self, elapsed):
        if elapsed <= 0:
            return
        hz = 1.0 / elapsed
        n = max(1, len(self.selected_pids))
        self.rate_label.setText(f"{hz:.1f} Hz · {n} PID")

    def on_sample(self, pid, value, unit):
        value, unit = convert_for_display(value, unit)
        row = self.rows_by_pid.get(pid)
        display = "—" if value is None else (
            f"{value:g}" if isinstance(value, (int, float)) else str(value)
        )

        if row is not None:
            item = self.table.item(row, 2)
            if item is None:
                self.table.setItem(row, 2, QTableWidgetItem(display))
            elif item.text() != display:
                item.setText(display)

        gauge = self.gauges_by_pid.get(pid)
        if gauge and isinstance(value, (int, float)):
            gauge.set_value(value)

        if pid == self.graphed_pid and isinstance(value, (int, float)):
            self.graph.add_value(value)

        if self.recording and value is not None:
            entry = get_pid(pid)
            name = entry["name"] if entry else f"PID {pid:02X}"
            self.recorded_samples.append({
                "tempo": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "parametro": name,
                "valor": value,
                "unidade": unit,
            })
            self.export_live_button.setEnabled(True)

    def toggle_recording(self):
        self.recording = self.record_button.isChecked()
        if self.recording:
            self.record_button.setText("⏺   A Gravar...")
        else:
            self.record_button.setText("⏺   Gravar")

    def export_recording(self):
        if not self.recorded_samples:
            return
        path, _filter = QFileDialog.getSaveFileName(
            self, "Exportar Dados em Tempo Real", "dados_tempo_real.csv",
            "CSV (*.csv)"
        )
        if not path:
            return
        try:
            export_live_data_csv(path, self.recorded_samples)
        except Exception as error:
            QMessageBox.warning(self, "Erro ao exportar", str(error))
