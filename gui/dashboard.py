from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
)

from gui.widgets import StatCard, page_header
from gui.styles import (
    CARD_BG,
    CARD_BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    SUCCESS,
    WARNING,
    DANGER,
    get_current_accent,
    get_theme_colors,
)


class Dashboard(QWidget):
    """Página principal: visão rápida da sessão e acesso às funções principais.

    O Dashboard não duplica ferramentas de diagnóstico. Serve como cockpit da
    aplicação: estado da ligação, veículo, indicadores essenciais e atalhos.
    """

    goToConnection = Signal()
    goToDTC = Signal()
    goToLiveData = Signal()
    goToReadiness = Signal()

    def __init__(self):
        super().__init__()

        # Resolvida uma vez à construção — reflete sempre o tema
        # guardado pelo utilizador, em vez da cor de destaque fixa.
        self._accent = get_current_accent()
        self._colors = get_theme_colors(self._accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(page_header(
            "Dashboard",
            "Centro de controlo da sessão de diagnóstico"
        ))

        self.content = QVBoxLayout()
        self.content.setSpacing(16)
        layout.addLayout(self.content)
        layout.addStretch()

        self.connected = False
        self._build_views()
        self.set_connection_state("disconnected")

    def _build_views(self):
        self.welcome_view = self.build_welcome_view()
        self.connected_view = self.build_connected_view()
        self.content.addWidget(self.welcome_view)
        self.content.addWidget(self.connected_view)

    # ------------------------------------------------------------------
    # Ecrã sem ligação
    # ------------------------------------------------------------------

    def build_welcome_view(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("dashboardHero")
        hero.setStyleSheet(f"""
        #dashboardHero {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {self._colors["accent_soft"]},
                stop:0.55 {self._colors["accent_soft_light"]},
                stop:1 rgba(20, 25, 32, 0.95)
            );
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
        }}
        """)

        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(30, 28, 30, 28)
        hero_layout.setSpacing(24)

        mark = QFrame()
        mark.setFixedSize(62, 62)
        mark.setStyleSheet(f"""
        QFrame {{
            background: {self._colors["accent_soft"]};
            border: 1px solid {self._colors["accent_border"]};
            border-radius: 16px;
        }}
        """)
        mark_layout = QVBoxLayout(mark)
        mark_layout.setContentsMargins(0, 0, 0, 0)
        mark_label = QLabel("RAD")
        mark_label.setAlignment(Qt.AlignCenter)
        mark_label.setStyleSheet(
            f"font-size: 15px; font-weight: 900; color: {self._accent}; "
            "letter-spacing: 1px; background: transparent;"
        )
        mark_layout.addWidget(mark_label)

        text = QVBoxLayout()
        text.setSpacing(6)

        eyebrow = QLabel("DIAGNÓSTICO AUTOMÓVEL")
        eyebrow.setStyleSheet(
            f"font-size: 10px; font-weight: 800; color: {self._accent}; "
            "letter-spacing: 1.8px; background: transparent;"
        )

        title = QLabel("Pronto para diagnosticar")
        title.setStyleSheet(
            f"font-size: 24px; font-weight: 850; color: {TEXT}; "
            "background: transparent;"
        )

        subtitle = QLabel(
            "Liga uma interface OBD para identificar o veículo e iniciar uma "
            "sessão de diagnóstico."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM}; background: transparent;"
        )

        text.addWidget(eyebrow)
        text.addWidget(title)
        text.addWidget(subtitle)

        hero_layout.addWidget(mark, 0, Qt.AlignTop)
        hero_layout.addLayout(text, 1)

        button = QPushButton("Ligar ao Veículo")
        button.setObjectName("primaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumSize(170, 44)
        button.clicked.connect(self.goToConnection.emit)
        hero_layout.addWidget(button, 0, Qt.AlignVCenter)

        layout.addWidget(hero)

        info = QFrame()
        info.setObjectName("dashboardInfo")
        info.setStyleSheet(f"""
        #dashboardInfo {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
        }}
        """)
        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(28)

        items = [
            ("01", "LIGAÇÃO", "Detectar interface e iniciar sessão"),
            ("02", "IDENTIFICAÇÃO", "Obter veículo, VIN e protocolo"),
            ("03", "DIAGNÓSTICO", "Ler falhas e parâmetros em tempo real"),
        ]

        for number, heading, description in items:
            block = QVBoxLayout()
            block.setSpacing(3)

            number_label = QLabel(number)
            number_label.setStyleSheet(
                f"font-size: 10px; font-weight: 900; color: {self._accent}; "
                "background: transparent;"
            )
            heading_label = QLabel(heading)
            heading_label.setStyleSheet(
                f"font-size: 10px; font-weight: 800; color: {TEXT}; "
                "letter-spacing: 1px; background: transparent;"
            )
            desc_label = QLabel(description)
            desc_label.setStyleSheet(
                f"font-size: 11px; color: {TEXT_FAINT}; background: transparent;"
            )

            block.addWidget(number_label)
            block.addWidget(heading_label)
            block.addWidget(desc_label)
            info_layout.addLayout(block, 1)

        layout.addWidget(info)
        return wrapper

    # ------------------------------------------------------------------
    # Ecrã ligado
    # ------------------------------------------------------------------

    def build_connected_view(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(self.build_vehicle_card())

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self.connection_card = StatCard("LINK", "Estado da Ligação", "Ligado", accent=SUCCESS)
        self.pids_card = StatCard("PID", "PIDs Suportados", "—", accent=self._accent)
        self.dtc_card = StatCard("DTC", "Códigos de Falha", "—", accent=TEXT_FAINT)
        self.voltage_card = StatCard("V", "Tensão da Bateria", "—", accent=TEXT_FAINT)

        for card in (self.connection_card, self.pids_card, self.dtc_card, self.voltage_card):
            cards_row.addWidget(card, 1)

        layout.addLayout(cards_row)
        layout.addWidget(self.build_quick_actions())
        return wrapper

    def build_vehicle_card(self):
        card = QFrame()
        card.setObjectName("dashboardVehicle")
        card.setStyleSheet(f"""
        #dashboardVehicle {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {self._colors["accent_soft"]},
                stop:1 {self._colors["accent_soft_light"]}
            );
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
        }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        identity = QVBoxLayout()
        identity.setSpacing(4)

        eyebrow = QLabel("VEÍCULO DETECTADO")
        eyebrow.setStyleSheet(
            f"font-size: 10px; font-weight: 800; color: {self._accent}; "
            "letter-spacing: 1.5px; background: transparent;"
        )

        self.vehicle = QLabel("Veículo não identificado")
        self.vehicle.setStyleSheet(
            f"font-size: 22px; font-weight: 850; color: {TEXT}; background: transparent;"
        )

        self.vin = QLabel("VIN  —")
        self.protocol = QLabel("Protocolo  —")
        self.voltage = QLabel("Bateria  —")

        for label in (self.vin, self.protocol, self.voltage):
            label.setStyleSheet(
                f"font-size: 11px; color: {TEXT_DIM}; background: transparent;"
            )

        identity.addWidget(eyebrow)
        identity.addWidget(self.vehicle)
        identity.addSpacing(4)

        details = QHBoxLayout()
        details.setSpacing(18)
        details.addWidget(self.vin)
        details.addWidget(self.protocol)
        details.addWidget(self.voltage)
        details.addStretch()
        identity.addLayout(details)

        status = QVBoxLayout()
        status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status.setSpacing(4)

        self.connection_status = QLabel("LIGADO")
        self.connection_status.setAlignment(Qt.AlignRight)
        self.connection_status.setStyleSheet(
            f"font-size: 11px; font-weight: 900; color: {SUCCESS}; "
            "letter-spacing: 1.2px; background: transparent;"
        )

        self.session_info = QLabel("Sessão activa")
        self.session_info.setAlignment(Qt.AlignRight)
        self.session_info.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DIM}; background: transparent;"
        )

        status.addWidget(self.connection_status)
        status.addWidget(self.session_info)

        layout.addLayout(identity, 1)
        layout.addLayout(status)
        return card

    def build_quick_actions(self):
        card = QFrame()
        card.setObjectName("dashboardActions")
        card.setStyleSheet(f"""
        #dashboardActions {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
        }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(10)

        title = QLabel("DIAGNÓSTICO")
        title.setStyleSheet(
            f"font-size: 10px; font-weight: 800; color: {TEXT_DIM}; "
            "letter-spacing: 1.5px; background: transparent;"
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)

        self.dtc_button = self.action_button(
            "Códigos de Falha",
            "Ler e analisar DTCs",
            accent=DANGER,
        )
        self.live_button = self.action_button(
            "Dados em Tempo Real",
            "Monitorizar sensores e PIDs",
            accent=self._accent,
        )
        self.readiness_button = self.action_button(
            "Prontidão",
            "Verificar monitores OBD-II",
            accent=SUCCESS,
        )
        self.connection_button = self.action_button(
            "Alterar Ligação",
            "Interface ou porta COM",
            accent=WARNING,
        )

        grid.addWidget(self.dtc_button, 0, 0)
        grid.addWidget(self.live_button, 0, 1)
        grid.addWidget(self.readiness_button, 1, 0)
        grid.addWidget(self.connection_button, 1, 1)

        self.dtc_button.clicked.connect(self.goToDTC.emit)
        self.live_button.clicked.connect(self.goToLiveData.emit)
        self.readiness_button.clicked.connect(self.goToReadiness.emit)
        self.connection_button.clicked.connect(self.goToConnection.emit)

        layout.addLayout(grid)
        return card

    def action_button(self, title, description, accent=None):
        accent = accent or self._accent
        button = QPushButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(54)
        button.setText(f"{title}\n{description}")
        button.setStyleSheet(f"""
        QPushButton {{
            text-align: left;
            padding: 8px 13px;
            border-radius: 9px;
            border: 1px solid {CARD_BORDER};
            border-left: 3px solid {accent};
            background: {CARD_BG};
            color: {TEXT};
            font-size: 12px;
            font-weight: 700;
        }}
        QPushButton:hover {{
            border-color: {accent};
            background: rgba(255, 255, 255, 0.025);
        }}
        QPushButton:pressed {{
            background: rgba(255, 255, 255, 0.045);
        }}
        """)
        return button

    # ------------------------------------------------------------------

    def update_vehicle(self, vehicle):
        vin = getattr(vehicle, "vin", None)
        make = getattr(vehicle, "make", None)
        model = getattr(vehicle, "model", None)
        protocol = getattr(vehicle, "protocol", None)
        voltage = getattr(vehicle, "battery_voltage", None)

        if make or model:
            self.vehicle.setText(f"{make or ''} {model or ''}".strip())
        elif vin:
            self.vehicle.setText("Veículo identificado")

        self.vin.setText(f"VIN  {vin}" if vin else "VIN  —")
        self.protocol.setText(f"Protocolo  {protocol}" if protocol else "Protocolo  —")

        if voltage is not None:
            accent = DANGER if voltage < 11.5 else WARNING if voltage > 15.0 else SUCCESS
            self.voltage.setText(f"Bateria  {voltage:g} V")
            self.voltage.setStyleSheet(
                f"font-size: 11px; color: {accent}; font-weight: 800; background: transparent;"
            )
            self.voltage_card.set_value(f"{voltage:g} V", accent=accent)

    def set_connection_state(self, state):
        states = {
            "connected": ("LIGADO", "Sessão activa", SUCCESS),
            "connecting": ("A LIGAR...", "A estabelecer comunicação", WARNING),
            "error": ("ERRO", "Falha na ligação", DANGER),
            "disconnected": ("SEM LIGAÇÃO", "Pronto para iniciar", TEXT_FAINT),
        }
        status, info, color = states.get(state, states["disconnected"])

        self.connected = state == "connected"
        self.welcome_view.setVisible(not self.connected)
        self.connected_view.setVisible(self.connected)

        self.connection_status.setText(status)
        self.connection_status.setStyleSheet(
            f"font-size: 11px; font-weight: 900; color: {color}; "
            "letter-spacing: 1.2px; background: transparent;"
        )
        self.session_info.setText(info)

        self.connection_card.set_value(
            "Ligado" if self.connected else status.title(),
            accent=color,
        )

        if state == "disconnected":
            self.pids_card.set_value("—", accent=self._accent)
            self.dtc_card.set_value("—", accent=TEXT_FAINT)
            self.voltage_card.set_value("—", accent=TEXT_FAINT)
            self.vehicle.setText("Veículo não identificado")
            self.vin.setText("VIN  —")
            self.protocol.setText("Protocolo  —")
            self.voltage.setText("Bateria  —")
            self.voltage.setStyleSheet(
                f"font-size: 11px; color: {TEXT_DIM}; background: transparent;"
            )

    def set_modules_count(self, count):
        self.pids_card.set_value(str(count), accent=self._accent)

    def set_faults_count(self, count):
        self.dtc_card.set_value(str(count), accent=DANGER if count else SUCCESS)
