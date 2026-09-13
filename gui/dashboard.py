from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStackedWidget
)

from gui.widgets import StatCard, page_header
from gui.styles import (
    CARD_BG,
    CARD_BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    ACCENT,
    SUCCESS,
    WARNING,
    DANGER
)


class Dashboard(QWidget):

    goToConnection = Signal()

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(page_header(
            "Ecra Principal",
            "Dados do diagnóstico atual"
        ))

        self.stack = QStackedWidget()
        self.stack.addWidget(self.build_welcome_view())
        self.stack.addWidget(self.build_connected_view())

        layout.addWidget(self.stack, 1)

        self.set_connection_state("disconnected")

    # ------------------------------------------------------------------
    # Estado sem ligação — ecrã de boas-vindas com atalhos rápidos
    # ------------------------------------------------------------------

    def build_welcome_view(self):

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(20)

        hero = QFrame()
        hero.setObjectName("heroCard")
        hero.setStyleSheet("""
        #heroCard {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(34, 211, 201, 0.14),
                stop:1 rgba(34, 211, 201, 0.02)
            );
            border: 1px solid #1E2530;
            border-radius: 14px;
        }
        """)

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(32, 34, 32, 34)
        hero_layout.setSpacing(10)
        hero_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("🩺")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 42px; background: transparent;")

        title = QLabel("Bem-vindo ao Roots Auto Doctor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 21px; font-weight: 800; color: {TEXT}; background: transparent;"
        )

        subtitle = QLabel(
            "Ainda não há nenhum veículo ligado."
            "Liga um adaptador OBD-II para começares a diagnosticar — sem ligação "
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(460)
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM}; background: transparent;"
        )

        button = QPushButton("⚡  Ligar ao Veículo")
        button.setObjectName("primaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(42)
        button.setMinimumWidth(220)
        button.clicked.connect(self.goToConnection.emit)

        hero_layout.addWidget(icon)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addSpacing(6)
        hero_layout.addWidget(button, 0, Qt.AlignCenter)

        layout.addWidget(hero)

        layout.addWidget(self.build_steps_card())
        layout.addStretch()

        return wrapper

    def build_steps_card(self):

        card = QFrame()
        card.setObjectName("stepsCard")
        card.setStyleSheet(f"""
        #stepsCard {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        title = QLabel("COMO COMEÇAR")
        title.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {TEXT_DIM}; "
            f"letter-spacing: 1px; background: transparent;"
        )
        layout.addWidget(title)

        steps = [
            ("1", "Liga o adaptador ELM327/OBD-II à tomada de diagnóstico do veículo (normalmente sob o volante)."),
            ("2", "Com a chave na posição \"Ignição\" (ou motor ligado), vai a \"Ligação\" e seleciona a porta."),
            ("3", "Depois de ligado, usa \"Códigos de Falha\", \"Dados em Tempo Real\" e \"Prontidão\" para diagnosticar."),
        ]

        for number, text in steps:
            layout.addWidget(self._step_row(number, text))

        return card

    def _step_row(self, number, text):

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        badge = QLabel(number)
        badge.setFixedSize(24, 24)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
        background: {ACCENT};
        color: #06181A;
        border-radius: 12px;
        font-weight: 800;
        font-size: 12px;
        """)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")

        row_layout.addWidget(badge, 0, Qt.AlignTop)
        row_layout.addWidget(label, 1)

        return row

    # ------------------------------------------------------------------
    # Estado com ligação — resumo real do veículo e da sessão
    # ------------------------------------------------------------------

    def build_connected_view(self):

        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        layout.addWidget(self.build_vehicle_card())

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.connection_card = StatCard(
            "🔌", "Ligação", "Desligado", accent=TEXT_FAINT
        )
        self.pids_card = StatCard(
            "📡", "PIDs Suportados", "—", accent=ACCENT
        )
        self.dtc_card = StatCard(
            "⚠", "Códigos de Falha", "—", accent=TEXT_FAINT
        )

        for card in (self.connection_card, self.pids_card, self.dtc_card):
            cards_row.addWidget(card)

        layout.addLayout(cards_row)

        hint = QLabel(
            "Usa \"Códigos de Falha\" para ler e filtrar DTCs por sistema, "
            "\"Dados em Tempo Real\" para monitorizar sensores ao vivo, e "
            "\"Prontidão\" antes de uma inspeção."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: 12px; padding-top: 4px;"
        )
        layout.addWidget(hint)

        layout.addStretch()

        return wrapper

    def build_vehicle_card(self):

        card = QFrame()
        card.setObjectName("vehicleCard")

        card.setStyleSheet("""
        #vehicleCard {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(34, 211, 201, 0.10),
                stop:1 rgba(34, 211, 201, 0.02)
            );
            border: 1px solid #1E2530;
            border-radius: 12px;
        }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(6)

        self.vehicle = QLabel("Veículo não identificado")
        self.vehicle.setStyleSheet(
            "font-size: 21px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(self.vehicle)

        info_row = QHBoxLayout()
        info_row.setSpacing(18)

        self.vin = QLabel("VIN  —")
        self.protocol = QLabel("Protocolo  —")

        for label in (self.vin, self.protocol):
            label.setStyleSheet(
                f"color: {TEXT_DIM}; font-size: 12px; background: transparent;"
            )
            info_row.addWidget(label)

        info_row.addStretch()
        layout.addLayout(info_row)

        return card

    # ------------------------------------------------------------------

    def update_vehicle(self, vehicle):

        if vehicle.vin:
            self.vin.setText(f"VIN  {vehicle.vin}")

        if vehicle.make:
            self.vehicle.setText(
                f"{vehicle.make} {vehicle.model or ''}".strip()
            )

        if vehicle.protocol:
            self.protocol.setText(f"Protocolo  {vehicle.protocol}")

    def set_connection_state(self, state):

        labels = {
            "connected": "Ligado",
            "connecting": "A ligar...",
            "error": "Erro",
            "disconnected": "Desligado",
        }

        colors = {
            "connected": SUCCESS,
            "connecting": WARNING,
            "error": DANGER,
            "disconnected": TEXT_FAINT,
        }

        self.stack.setCurrentIndex(1 if state == "connected" else 0)

        if state == "disconnected":
            # limpa o resumo da sessão anterior para não mostrar
            # valores "presos" de uma ligação já terminada
            self.pids_card.set_value("—")
            self.dtc_card.set_value("—", accent=TEXT_FAINT)
            self.vehicle.setText("Veículo não identificado")
            self.vin.setText("VIN  —")
            self.protocol.setText("Protocolo  —")

        self.connection_card.set_value(
            labels.get(state, "Desligado"),
            accent=colors.get(state, TEXT_FAINT)
        )

    def set_modules_count(self, count):
        self.pids_card.set_value(str(count))

    def set_faults_count(self, count):
        accent = DANGER if count else SUCCESS
        self.dtc_card.set_value(str(count), accent=accent)
