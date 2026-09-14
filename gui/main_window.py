from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QFrame,
    QButtonGroup,
    QGraphicsOpacityEffect
)

from gui.dashboard import Dashboard
from gui.connection import ConnectionPage
from gui.modules import ModulesPage
from gui.dtc import DTCPage
from gui.live_data import LiveDataPage
from gui.readiness import ReadinessPage
from gui.graphs import GraphsPage
from gui.logs import LogsPage
from gui.widgets import StatusPill, SectionLabel
from gui.styles import (
    BG_SIDEBAR,
    BG_TOPBAR,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    ACCENT,
    DIVIDER
)
from app.config import APP_VERSION


# (ícone, nome, subtítulo mostrado na barra superior, classe da página)
NAV_ITEMS = [
    ("🏠", "Dashboard", "Visão geral da sessão de diagnóstico", Dashboard),
    ("🔌", "Ligação", "Interface de diagnóstico (ELM327 / KKL / J2534)", ConnectionPage),
    ("🧩", "Módulos", "Informação da passarela de diagnóstico (gateway) OBD-II", ModulesPage),
    ("⚠", "Códigos de Falha", "Leitura e limpeza de DTCs", DTCPage),
    ("📡", "Dados em Tempo Real", "Parâmetros ao vivo (PIDs)", LiveDataPage),
    ("🛡", "Prontidão", "Verificação para inspeção / emissões", ReadinessPage),
    ("📈", "Gráficos", "Monitorização gráfica dos parâmetros", GraphsPage),
    ("🧾", "Registo", "Log de comunicação com a centralina", LogsPage),
]

# Agrupamento visual da sidebar: (rótulo da secção, índices em NAV_ITEMS)
NAV_SECTIONS = [
    ("Início", [0, 1]),
    ("Leitura OBD-II", [2, 3, 4, 5]),
    ("Sistema", [6, 7]),
]


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Roots Auto Doctor")
        self.resize(1300, 820)
        self.setMinimumSize(1080, 680)

        self.pages = QStackedWidget()
        self.page_widgets = []

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.build()

    def build(self):

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self.build_sidebar())
        root.addWidget(self.build_content(), 1)

        self.statusBar().showMessage("Pronto")

        # Liga o sinal da página de Ligação ao resto da app.
        self.connection_page.connectionChanged.connect(
            self.on_connection_changed
        )
        self.connection_page.protocolReady.connect(
            self.on_protocol_ready
        )
        self.connection_page.logLine.connect(
            self.logs_page.append_line
        )
        self.dtc_page.dtcsChanged.connect(
            self.dashboard_page.set_faults_count
        )

        # Qualquer página bloqueada por falta de ligação leva o
        # utilizador diretamente à página de Ligação.
        for page in (self.dtc_page, self.live_data_page, self.readiness_page,
                     self.modules_page, self.graphs_page):
            page.gate.goToConnection.connect(self.go_to_connection)

        self.dashboard_page.goToConnection.connect(self.go_to_connection)

        self.nav_group.button(0).setChecked(True)
        self.on_nav_changed(0)

    def build_sidebar(self):

        sidebar = QFrame()
        sidebar.setFixedWidth(240)

        sidebar.setStyleSheet(f"""
        QFrame {{
            background: {BG_SIDEBAR};
            border-right: 1px solid {DIVIDER};
        }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(4)

        brand = QLabel("⚙  ROOTS")
        brand.setStyleSheet(
            f"font-size: 19px; font-weight: 800; color: {TEXT}; "
            f"letter-spacing: 1px;"
        )

        tagline = QLabel("AUTO DOCTOR · ECU SCAN")
        tagline.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {ACCENT}; "
            f"letter-spacing: 2px; padding-left: 2px;"
        )

        layout.addWidget(brand)
        layout.addWidget(tagline)
        layout.addSpacing(22)

        for index, (icon, name, _subtitle, page_class) in enumerate(NAV_ITEMS):

            page = page_class()
            self.page_widgets.append(page)
            self.pages.addWidget(page)

        # Referências diretas às páginas que precisam de comunicar
        # entre si (Ligação -> Dashboard / Módulos / DTCs / Live Data).
        self.dashboard_page = self.page_widgets[0]
        self.connection_page = self.page_widgets[1]
        self.modules_page = self.page_widgets[2]
        self.dtc_page = self.page_widgets[3]
        self.live_data_page = self.page_widgets[4]
        self.readiness_page = self.page_widgets[5]
        self.graphs_page = self.page_widgets[6]
        self.logs_page = self.page_widgets[7]

        for section_label, indexes in NAV_SECTIONS:

            layout.addWidget(SectionLabel(section_label))

            for index in indexes:

                icon, name, _subtitle, _page_class = NAV_ITEMS[index]

                button = QPushButton(f"   {icon}    {name}")
                button.setObjectName("navButton")
                button.setCheckable(True)
                button.setMinimumHeight(42)
                button.setCursor(Qt.PointingHandCursor)

                self.nav_group.addButton(button, index)
                button.clicked.connect(
                    lambda _checked, i=index: self.on_nav_changed(i)
                )

                layout.addWidget(button)

        layout.addStretch()

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {DIVIDER}; border: none;")
        layout.addWidget(divider)
        layout.addSpacing(10)

        version = QLabel(f"Roots Auto Doctor  ·  v{APP_VERSION}")
        version.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 11px; padding: 4px 2px;"
        )
        layout.addWidget(version)

        return sidebar

    def build_content(self):

        content = QWidget()

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.build_topbar())

        pages_wrapper = QWidget()
        pages_layout = QVBoxLayout(pages_wrapper)
        pages_layout.setContentsMargins(32, 26, 32, 24)
        pages_layout.addWidget(self.pages)

        layout.addWidget(pages_wrapper, 1)

        return content

    def build_topbar(self):

        topbar = QFrame()
        topbar.setFixedHeight(58)

        topbar.setStyleSheet(f"""
        QFrame {{
            background: {BG_TOPBAR};
            border-bottom: 1px solid {DIVIDER};
        }}
        """)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(28, 0, 22, 0)
        layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(0)

        self.page_title = QLabel()
        self.page_title.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {TEXT};"
        )

        self.page_subtitle = QLabel()
        self.page_subtitle.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DIM};"
        )

        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)

        title_wrap = QWidget()
        title_wrap.setLayout(title_box)

        layout.addWidget(title_wrap)
        layout.addStretch()

        self.topbar_status = StatusPill("disconnected")
        layout.addWidget(self.topbar_status)

        return topbar

    def on_nav_changed(self, index):

        self.pages.setCurrentIndex(index)

        _icon, name, subtitle, _cls = NAV_ITEMS[index]

        self.page_title.setText(name)
        self.page_subtitle.setText(subtitle)

        self._animate_page_in()

    def go_to_connection(self):

        self.nav_group.button(1).setChecked(True)
        self.on_nav_changed(1)

    def _animate_page_in(self):

        current = self.pages.currentWidget()

        effect = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(effect)

        self._page_animation = QPropertyAnimation(effect, b"opacity")
        self._page_animation.setDuration(220)
        self._page_animation.setStartValue(0.0)
        self._page_animation.setEndValue(1.0)
        self._page_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._page_animation.start()

    def on_connection_changed(self, state, message):

        self.topbar_status.set_state(state)
        self.dashboard_page.set_connection_state(state)
        self.statusBar().showMessage(message)

    def on_protocol_ready(self, protocol, info):

        info = info or {}

        self.dtc_page.set_protocol(protocol, info)
        self.live_data_page.set_protocol(protocol)
        self.readiness_page.set_protocol(protocol)
        self.modules_page.set_protocol(protocol, info)
        self.graphs_page.set_protocol(protocol)

        vehicle = info.get("vehicle")
        if vehicle:
            self.dashboard_page.update_vehicle(vehicle)

        pid_count = info.get("supported_pid_count", 0)
        self.dashboard_page.set_modules_count(pid_count)
