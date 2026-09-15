from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QLabel
)

from gui.widgets import page_header, empty_hint, CategoryTabs, SeverityBadge, page_with_gate
from gui.styles import TEXT_FAINT, TEXT_DIM, DANGER, SUCCESS
from services.dtc_database import CATEGORY_NAMES, CATEGORY_ICONS, build_dtc
from services.session_export import export_dtcs_csv
from services.pid_database import get_pid
from services.units import convert_for_display

CATEGORY_LOOKUP = {
    "Todas": None,
    f"{CATEGORY_ICONS['P']} Motor": "P",
    f"{CATEGORY_ICONS['C']} Travagem / ABS": "C",
    f"{CATEGORY_ICONS['B']} Carroçaria / Airbag": "B",
    f"{CATEGORY_ICONS['U']} Rede / Comunicação": "U",
}


class DTCReadWorker(QThread):
    finished_ok = Signal(list, list, list)
    failed = Signal(str)

    def __init__(self, protocol):
        super().__init__()
        self.protocol = protocol

    def run(self):
        try:
            confirmed = self.protocol.trouble_codes(pending=False)
            pending = self.protocol.trouble_codes(pending=True)
            permanent = self.protocol.trouble_codes(permanent=True)
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished_ok.emit(confirmed, pending, permanent)


class DTCPage(QWidget):

    dtcsChanged = Signal(int)

    def __init__(self):
        super().__init__()

        self.protocol = None
        self.dtcs = []
        self.vehicle_info = {}
        self.visible_dtcs = []
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(page_header(
            "Códigos de Falha",
            "Lê e apaga os DTCs guardados nas centralinas. Usa as abas "
            "abaixo para veres só os códigos de um sistema — por "
            "exemplo, só o ABS ou só o Airbag."
        ))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.read_button = QPushButton("🔍   Ler Códigos de Falha")
        self.read_button.setObjectName("primaryButton")
        self.read_button.setMinimumHeight(38)
        self.read_button.setCursor(Qt.PointingHandCursor)
        self.read_button.clicked.connect(self.read_dtcs)

        self.clear_button = QPushButton("🗑   Apagar Códigos")
        self.clear_button.setObjectName("dangerButton")
        self.clear_button.setMinimumHeight(38)
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_dtcs)

        self.export_button = QPushButton("⬇   Exportar CSV")
        self.export_button.setMinimumHeight(38)
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.export_button.clicked.connect(self.export_csv)

        toolbar.addWidget(self.read_button)
        toolbar.addWidget(self.clear_button)
        toolbar.addWidget(self.export_button)
        toolbar.addStretch()

        content_layout.addLayout(toolbar)

        self.tabs = CategoryTabs(
            list(CATEGORY_LOOKUP.keys()),
            on_change=self.apply_filter
        )
        content_layout.addWidget(self.tabs)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Código", "Sistema", "Origem", "Descrição"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.show_freeze_frame)

        content_layout.addWidget(self.table)

        self.hint = empty_hint(
            "Faz duplo-clique num código para ver o freeze frame "
            "(sensores no momento da falha)."
        )
        content_layout.addWidget(self.hint)

        self.stack, self.gate = page_with_gate(
            content,
            "Liga-te ao veículo para leres os códigos de falha "
            "guardados nas centralinas."
        )
        layout.addWidget(self.stack, 1)

        self.set_protocol(None, {})

    def set_protocol(self, protocol, vehicle_info):
        self.protocol = protocol
        self.vehicle_info = vehicle_info or {}
        connected = protocol is not None
        self.stack.setCurrentIndex(1 if connected else 0)
        self.read_button.setEnabled(connected)
        self.clear_button.setEnabled(connected and bool(self.dtcs))
        self.export_button.setEnabled(bool(self.dtcs))
        if not connected:
            self.dtcs = []
            self.render_rows([])
            self.dtcsChanged.emit(0)

    def read_dtcs(self):
        if not self.protocol:
            return
        if self.worker and self.worker.isRunning():
            return

        self.read_button.setEnabled(False)
        self.read_button.setText("A ler...")

        self.worker = DTCReadWorker(self.protocol)
        self.worker.finished_ok.connect(self._on_dtcs_read)
        self.worker.failed.connect(self._on_dtcs_failed)
        self.worker.start()

    def _on_dtcs_read(self, confirmed_codes, pending_codes, permanent_codes):
        self.read_button.setEnabled(self.protocol is not None)
        self.read_button.setText("🔍   Ler Códigos de Falha")

        confirmed = set(confirmed_codes)
        permanent = set(permanent_codes)
        all_codes = list(dict.fromkeys(
            confirmed_codes + pending_codes + permanent_codes
        ))

        def status_of(code):
            if code in permanent:
                return "Permanente"
            if code in confirmed:
                return "Confirmado"
            return "Pendente"

        self.dtcs = [build_dtc(code, status=status_of(code)) for code in all_codes]
        self.clear_button.setEnabled(bool(self.dtcs))
        self.export_button.setEnabled(bool(self.dtcs))
        self.apply_filter(self.tabs.active)
        self.dtcsChanged.emit(len(self.dtcs))

    def _on_dtcs_failed(self, message):
        self.read_button.setEnabled(self.protocol is not None)
        self.read_button.setText("🔍   Ler Códigos de Falha")
        QMessageBox.warning(
            self, "Erro de leitura",
            f"Não foi possível ler os códigos de falha:\n{message}"
        )

    def clear_dtcs(self):
        if not self.protocol:
            return

        warning_extra = ""
        try:
            rpm, _unit = self.protocol.read_pid(0x0C)
            if rpm is not None and rpm > 0:
                warning_extra = (
                    "\n\n⚠ O motor parece estar a trabalhar (RPM > 0). "
                    "É recomendável desligar o motor antes de apagar "
                    "códigos de falha."
                )
        except Exception:
            pass

        confirm = QMessageBox.question(
            self, "Apagar códigos de falha",
            "Tens a certeza que queres apagar todos os códigos de falha "
            "guardados nas centralinas do veículo?\n\n"
            "Esta ação não pode ser desfeita." + warning_extra,
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.protocol.clear_trouble_codes()
        except Exception as error:
            QMessageBox.warning(
                self, "Erro", f"Não foi possível apagar os códigos:\n{error}"
            )
            return

        self.dtcs = []
        self.render_rows([])
        self.clear_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.dtcsChanged.emit(0)

    def export_csv(self):
        if not self.dtcs:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar relatório de códigos de falha",
            "relatorio_dtc.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            export_dtcs_csv(path, self.vehicle_info, self.dtcs)
        except Exception as error:
            QMessageBox.warning(self, "Erro ao exportar", str(error))

    def apply_filter(self, category_label):
        letter = CATEGORY_LOOKUP.get(category_label)
        if letter is None:
            filtered = self.dtcs
        else:
            filtered = [d for d in self.dtcs if d.category_letter == letter]

        self.render_rows(filtered)

        counts = {"Todas": len(self.dtcs)}
        for label, code_letter in CATEGORY_LOOKUP.items():
            if code_letter:
                counts[label] = len([
                    d for d in self.dtcs if d.category_letter == code_letter
                ])
        self.tabs.set_counts(counts)

    def render_rows(self, dtcs):
        self.visible_dtcs = dtcs
        self.table.setRowCount(0)

        for dtc in dtcs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            code_item = QTableWidgetItem(dtc.code)
            code_item.setForeground(QColor(SeverityBadge.COLORS.get(dtc.status, DANGER)))
            font = code_item.font()
            font.setBold(True)
            code_item.setFont(font)

            self.table.setItem(row, 0, code_item)
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(dtc.origin_label))
            self.table.setItem(row, 3, QTableWidgetItem(dtc.description))
            self.table.setCellWidget(row, 1, self._badge_cell(dtc))

    def _badge_cell(self, dtc):
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        icon = CATEGORY_ICONS.get(dtc.category_letter, "")
        layout.addWidget(_plain_label(f"{icon} {dtc.category}"))
        layout.addWidget(SeverityBadge(dtc.status))
        layout.addStretch()
        return wrapper

    def show_freeze_frame(self, row, _column):
        if not self.protocol or row >= len(self.visible_dtcs):
            return

        dtc = self.visible_dtcs[row]
        pids_of_interest = [0x0C, 0x0D, 0x05, 0x04, 0x11, 0x0B]
        lines = []

        for pid in pids_of_interest:
            try:
                value, unit = self.protocol.freeze_frame(pid)
            except Exception:
                continue
            if value is None:
                continue
            value, unit = convert_for_display(value, unit)
            entry = get_pid(pid)
            name = entry["name"] if entry else f"PID {pid:02X}"
            lines.append(f"{name}: {value} {unit}")

        if not lines:
            QMessageBox.information(
                self, f"Freeze Frame — {dtc.code}",
                "Este veículo não guardou dados de freeze frame "
                "para este código, ou o pedido não é suportado."
            )
            return

        QMessageBox.information(
            self, f"Freeze Frame — {dtc.code}",
            f"Fotografia dos sensores no momento da falha:\n\n" + "\n".join(lines)
        )


def _plain_label(text):
    label = QLabel(text)
    label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
    return label
