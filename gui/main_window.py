from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QCoreApplication
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
    QGraphicsOpacityEffect,
    QMessageBox,
    QDialog,
    QProgressBar
)

from gui.dashboard import Dashboard
from gui.system import SystemPage
from gui.modules import ModulesPage
from gui.dtc import DTCPage
from gui.live_data import LiveDataPage
from gui.readiness import ReadinessPage
from gui.graphs import GraphsPage
from gui.logs import LogsPage
from gui.widgets import StatusPill, SectionLabel
from gui.styles import (
    BG_SIDEBAR, BG_TOPBAR, TEXT, TEXT_DIM, TEXT_FAINT, DIVIDER,
    get_current_accent, get_settings
)
from app.config import APP_VERSION


# (ícone, nome, subtítulo mostrado na barra superior, classe da página)
NAV_ITEMS = [
    ("", "Dashboard", "Visão geral da sessão de diagnóstico", Dashboard),
    ("", "Módulos", "Informação da passarela de diagnóstico (gateway) OBD-II", ModulesPage),
    ("", "Códigos de Falha", "Leitura e limpeza de DTCs", DTCPage),
    ("", "Dados em Tempo Real", "Parâmetros ao vivo (PIDs)", LiveDataPage),
    ("", "Prontidão", "Verificação para inspeção / emissões", ReadinessPage),
    ("", "Gráficos", "Monitorização gráfica dos parâmetros", GraphsPage),
    ("", "Registo", "Log de comunicação com a centralina", LogsPage),
    ("", "Sistema", "Ligação OBD e definições da aplicação", SystemPage),
]

# Agrupamento visual da sidebar: (rótulo da secção, índices em NAV_ITEMS)
NAV_SECTIONS = [
    ("Início", [0]),
    ("Diagnóstico", [1, 2, 3, 4, 5, 6]),
    ("Sistema", [7]),
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
        self._closing = False
        self._page_animation = None

        self.build()

    def _is_vehicle_connected(self):
        """Devolve True quando existe uma ligação física ativa ao adaptador."""
        connection = getattr(self, "connection_page", None)
        manager = getattr(connection, "manager", None)
        connected = getattr(manager, "connected", None)

        try:
            return bool(connected()) if callable(connected) else False
        except Exception:
            return False

    def _show_close_confirmation(self):
        """Diálogo de confirmação com o mesmo aspeto da aplicação."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Fechar Roots Auto Doctor")
        dialog.setModal(True)
        dialog.setFixedWidth(460)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: {BG_TOPBAR};
                color: {TEXT};
            }}
            QPushButton {{
                min-height: 38px;
                padding: 0 18px;
                border-radius: 8px;
                border: 1px solid {DIVIDER};
                background: {BG_SIDEBAR};
                color: {TEXT};
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {get_current_accent()};
            }}
            QPushButton#closeConfirmButton {{
                background: {get_current_accent()};
                color: white;
                border: none;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(12)

        title = QLabel("Fechar Roots Auto Doctor")
        title.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {TEXT};")
        layout.addWidget(title)

        message = QLabel(
            "Tens a certeza que queres fechar a aplicação?\n\n"
            "A ligação ao veículo e qualquer monitorização ativa serão terminadas com segurança."
        )
        message.setWordWrap(True)
        message.setStyleSheet(f"font-size: 12px; color: {TEXT_DIM}; line-height: 1.4;")
        layout.addWidget(message)
        layout.addSpacing(8)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel = QPushButton("Cancelar")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(dialog.reject)

        confirm = QPushButton("Fechar aplicação")
        confirm.setObjectName("closeConfirmButton")
        confirm.setCursor(Qt.PointingHandCursor)
        confirm.setDefault(True)
        confirm.clicked.connect(dialog.accept)

        buttons.addWidget(cancel)
        buttons.addWidget(confirm)
        layout.addLayout(buttons)

        return dialog.exec() == QDialog.Accepted

    def _show_shutdown_dialog(self):
        """Mostra feedback visual enquanto os recursos são libertados."""
        dialog = QDialog(self)
        dialog.setWindowTitle("A encerrar")
        dialog.setModal(False)
        dialog.setFixedWidth(380)
        dialog.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        dialog.setStyleSheet(f"""
            QDialog {{ background: {BG_TOPBAR}; color: {TEXT}; }}
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: {BG_SIDEBAR};
                height: 7px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {get_current_accent()};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(10)

        title = QLabel("A encerrar Roots Auto Doctor")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {TEXT};")
        layout.addWidget(title)

        status = QLabel("A preparar o encerramento...")
        status.setStyleSheet(f"font-size: 12px; color: {TEXT_DIM};")
        status.setWordWrap(True)
        layout.addWidget(status)

        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        layout.addWidget(progress)

        dialog.show()
        QCoreApplication.processEvents()
        return dialog, status

    def closeEvent(self, event):
        """Fecha a aplicação de forma controlada e segura."""
        if self._closing:
            event.ignore()
            return

        settings = get_settings()
        confirm = settings.value("preferences/confirm_exit", True)
        if isinstance(confirm, str):
            confirm = confirm.strip().lower() in ("1", "true", "yes", "on")
        else:
            confirm = bool(confirm)

        if confirm and not self._show_close_confirmation():
            event.ignore()
            return

        self._closing = True
        shutdown_dialog = None

        try:
            shutdown_dialog, status = self._show_shutdown_dialog()
            self._shutdown_session(status.setText)
        except Exception as error:
            print(f"[Roots Auto Doctor] Erro no encerramento: {error}")
        finally:
            if shutdown_dialog is not None:
                shutdown_dialog.close()

        event.accept()

    def _shutdown_session(self, update_status=None):
        """Para monitorizações e fecha a ligação sem deixar a UI bloqueada."""
        def update(text):
            if update_status:
                update_status(text)
                QCoreApplication.processEvents()

        update("A terminar monitorizações ativas...")
        for page in (
            getattr(self, "live_data_page", None),
            getattr(self, "graphs_page", None),
        ):
            stop = getattr(page, "stop_stream", None)
            if callable(stop):
                try:
                    stop()
                except Exception as error:
                    print(f"[Roots Auto Doctor] Erro ao parar stream: {error}")

        connection = getattr(self, "connection_page", None)
        disconnect = getattr(connection, "disconnect", None)
        if callable(disconnect):
            update("A terminar a ligação ao veículo...")
            try:
                disconnect()
            except Exception as error:
                print(f"[Roots Auto Doctor] Erro ao desligar OBD: {error}")

        update("A libertar recursos...")

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
        self.system_page.appearance_page.accent_changed.connect(
            self.on_theme_changed
        )
        self.dtc_page.dtcsChanged.connect(
            self.dashboard_page.set_faults_count
        )
        self.live_data_page.streamStarted.connect(self.graphs_page.stop_stream)
        self.graphs_page.streamStarted.connect(self.live_data_page.stop_stream)

        # Qualquer página bloqueada por falta de ligação leva o
        # utilizador diretamente à página de Ligação.
        for page in (self.dtc_page, self.live_data_page, self.readiness_page,
                     self.modules_page, self.graphs_page):
            page.gate.goToConnection.connect(self.go_to_connection)

        self.dashboard_page.goToConnection.connect(self.go_to_connection)
        self.dashboard_page.goToDTC.connect(lambda: self.go_to(2))
        self.dashboard_page.goToLiveData.connect(lambda: self.go_to(3))
        self.dashboard_page.goToReadiness.connect(lambda: self.go_to(4))

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

        brand = QLabel("ROOTS")
        brand.setStyleSheet(
            f"font-size: 19px; font-weight: 800; color: {TEXT}; "
            f"letter-spacing: 1px;"
        )

        tagline = QLabel("AUTO DOCTOR · ECU SCAN")
        self.sidebar_tagline = tagline
        tagline.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {get_current_accent()}; "
            f"letter-spacing: 2px; padding-left: 2px;"
        )

        layout.addWidget(brand)
        layout.addWidget(tagline)
        layout.addSpacing(22)

        for index, (_icon, name, _subtitle, page_class) in enumerate(NAV_ITEMS):

            page = page_class()
            self.page_widgets.append(page)
            self.pages.addWidget(page)

        # Referências diretas às páginas que precisam de comunicar
        # entre si (Ligação -> Dashboard / Módulos / DTCs / Live Data).
        self.dashboard_page = self.page_widgets[0]
        self.modules_page = self.page_widgets[1]
        self.dtc_page = self.page_widgets[2]
        self.live_data_page = self.page_widgets[3]
        self.readiness_page = self.page_widgets[4]
        self.graphs_page = self.page_widgets[5]
        self.logs_page = self.page_widgets[6]
        self.system_page = self.page_widgets[7]
        self.connection_page = self.system_page.connection_page

        for section_label, indexes in NAV_SECTIONS:

            layout.addWidget(SectionLabel(section_label))

            for index in indexes:

                _icon, name, _subtitle, _page_class = NAV_ITEMS[index]

                button = QPushButton(f"   {name}")
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

    def go_to(self, index):

        self.nav_group.button(index).setChecked(True)
        self.on_nav_changed(index)

    def go_to_connection(self):

        self.nav_group.button(7).setChecked(True)
        self.system_page.show_connection()
        self.on_nav_changed(7)

    def _animate_page_in(self):

        current = self.pages.currentWidget()
        if current is None:
            return

        # A QGraphicsEffect becomes owned by the widget when assigned with
        # setGraphicsEffect(). Never call deleteLater() on the previous
        # effect: Qt may already have destroyed its C++ object when the
        # effect was replaced, leaving a dangling Shiboken wrapper.
        if self._page_animation is not None:
            self._page_animation.stop()
            self._page_animation = None

        # Remove any effect currently attached to this page before creating
        # a new one. Qt handles the lifetime of the previous effect.
        if current.graphicsEffect() is not None:
            current.setGraphicsEffect(None)

        effect = QGraphicsOpacityEffect()
        current.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(180)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        def finish_animation():
            # Only clear the effect if this animation still owns the effect
            # currently attached to this page. This prevents an older
            # animation from removing a newer effect after rapid navigation.
            if current.graphicsEffect() is effect:
                current.setGraphicsEffect(None)
            if self._page_animation is animation:
                self._page_animation = None

        animation.finished.connect(finish_animation)
        self._page_animation = animation
        animation.start()

    def on_theme_changed(self, accent):
        """Mantém componentes que guardam estado visual sincronizados."""
        accent = get_current_accent()
        self.sidebar_tagline.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {accent}; "
            "letter-spacing: 2px; padding-left: 2px;"
        )
        self.dashboard_page.refresh_theme(accent)

    def on_connection_changed(self, state, message):

        self.topbar_status.set_state(state)
        self.dashboard_page.set_connection_state(state)
        self.statusBar().showMessage(message)

    def on_protocol_ready(self, protocol, info):

        info = info or {}

        self.dtc_page.set_protocol(protocol, info)
        self.live_data_page.set_protocol(protocol, info)
        self.readiness_page.set_protocol(protocol)
        self.modules_page.set_protocol(protocol, info)
        self.graphs_page.set_protocol(protocol)

        vehicle = info.get("vehicle")
        if vehicle:
            self.dashboard_page.update_vehicle(vehicle)

        pid_count = info.get("supported_pid_count", 0)
        self.dashboard_page.set_modules_count(pid_count)
