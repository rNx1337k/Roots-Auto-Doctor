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
    QScrollArea
)

from gui.widgets import page_header, empty_hint, LiveGraph, Gauge, page_with_gate
from gui.styles import TEXT_FAINT, ACCENT, CARD_BORDER
from services.pid_database import PID_TABLE, ALL_CATEGORIES, get_pid
from app.config import LIVE_DATA_INTERVAL


class LiveDataWorker(QThread):
    """Lê, num thread próprio, os PIDs selecionados em ciclo contínuo,
    para não bloquear a interface enquanto espera pelo adaptador."""

    sample = Signal(int, object, str)   # pid, valor, unidade
    error = Signal(str)

    def __init__(self, protocol, pids, interval=LIVE_DATA_INTERVAL):

        super().__init__()

        self.protocol = protocol
        self.pids = pids
        self.interval = interval
        self._running = True

    def run(self):

        while self._running:

            for pid in list(self.pids):

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


class LiveDataPage(QWidget):

    def __init__(self):

        super().__init__()

        self.protocol = None
        self.worker = None
        self.selected_pids = set()
        self.rows_by_pid = {}
        self.graphed_pid = None
        self.gauges_by_pid = {}
        self.view_mode = "table"

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
            "\"Iniciar Leitura\"."
        ))

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para transmitires parâmetros em tempo real."
        )
        layout.addWidget(self.stack, 1)

        self.set_protocol(None)

    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------

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
        toolbar.addWidget(self.table_view_button)
        toolbar.addWidget(self.gauge_view_button)
        toolbar.addStretch()
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

            gauge = Gauge(entry["name"], entry["unit"], entry["min"], entry["max"])
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

        self.table.setRowCount(0)
        self.rows_by_pid = {}

        for entry in PID_TABLE:

            if category != "Todas" and entry["category"] != category:
                continue

            if term and term not in entry["name"].lower():
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

            self.table.setCellWidget(row, 0, cell)
            self.table.setItem(row, 1, QTableWidgetItem(entry["name"]))
            self.table.setItem(row, 2, QTableWidgetItem("—"))
            self.table.setItem(row, 3, QTableWidgetItem(entry["unit"]))

            graph_button = QPushButton("📈")
            graph_button.setCursor(Qt.PointingHandCursor)
            graph_button.setFixedWidth(50)
            graph_button.clicked.connect(
                lambda _checked, pid=entry["pid"]: self.show_in_graph(pid)
            )
            self.table.setCellWidget(row, 4, graph_button)

            self.rows_by_pid[entry["pid"]] = row

    # ------------------------------------------------------------------
    # Ligação ao protocolo
    # ------------------------------------------------------------------

    def set_protocol(self, protocol):

        self.stop_stream()
        self.protocol = protocol
        self.start_button.setEnabled(protocol is not None)
        self.stack.setCurrentIndex(1 if protocol is not None else 0)

    def toggle_pid(self, pid, state):

        if state:
            self.selected_pids.add(pid)
        else:
            self.selected_pids.discard(pid)

        if self.worker and self.worker.isRunning():
            self.worker.pids = list(self.selected_pids)

    def show_in_graph(self, pid):

        from services.pid_database import get_pid

        entry = get_pid(pid)

        if not entry:
            return

        self.graphed_pid = pid
        self.graph.set_series(
            entry["name"], entry["unit"], entry["min"], entry["max"]
        )

    def start_stream(self):

        if not self.protocol or not self.selected_pids:
            return

        self.worker = LiveDataWorker(self.protocol, list(self.selected_pids))
        self.worker.sample.connect(self.on_sample)
        self.worker.start()

        self.refresh_gauges()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_stream(self):

        if self.worker:
            self.worker.stop()
            self.worker.wait(1500)
            self.worker = None

        self.start_button.setEnabled(self.protocol is not None and bool(self.selected_pids))
        self.stop_button.setEnabled(False)

    def on_sample(self, pid, value, unit):

        row = self.rows_by_pid.get(pid)

        display = "—" if value is None else f"{value:g}" if isinstance(value, (int, float)) else str(value)

        if row is not None:
            self.table.setItem(row, 2, QTableWidgetItem(display))

        gauge = self.gauges_by_pid.get(pid)
        if gauge and isinstance(value, (int, float)):
            gauge.set_value(value)

        if pid == self.graphed_pid and isinstance(value, (int, float)):
            self.graph.add_value(value)
