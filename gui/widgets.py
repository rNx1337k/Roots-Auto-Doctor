"""
Componentes reutilizáveis usados em várias páginas
(pill de estado de ligação, cartões de estatística, cabeçalho de página).
"""

import math

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QGraphicsOpacityEffect
)

from gui.styles import (
    CARD_BG,
    CARD_BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    SUCCESS,
    WARNING,
    DANGER,
    get_current_accent
)


class StatusPill(QFrame):
    """Pequena pastilha com bolinha colorida + texto, usada para
    mostrar o estado da ligação ao veículo em qualquer página."""

    STATES = {
        "connected": (SUCCESS, "Ligado"),
        "disconnected": (TEXT_FAINT, "Sem ligação"),
        "connecting": (WARNING, "A ligar..."),
        "error": (DANGER, "Erro de ligação"),
    }

    def __init__(self, state="disconnected", parent=None):

        super().__init__(parent)

        self.setObjectName("statusPill")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 14, 7)
        layout.setSpacing(8)

        self._dot = QLabel("●")
        self._label = QLabel()

        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        self.set_state(state)

    def set_state(self, state, text=None):

        color, default_text = self.STATES.get(
            state, self.STATES["disconnected"]
        )

        self._dot.setStyleSheet(
            f"color: {color}; font-size: 10px; background: transparent;"
        )

        self._label.setText(text or default_text)

        self._label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; "
            f"background: transparent;"
        )

        self.setStyleSheet(f"""
        #statusPill {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 14px;
        }}
        """)

        self._pulse()

    def _pulse(self):

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(280)
        self._animation.setStartValue(0.3)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()


class StatCard(QFrame):
    """Cartão compacto com ícone, título e valor — usado no Dashboard."""

    def __init__(self, icon, title, value="—", accent=None):

        super().__init__()

        self._accent = accent or get_current_accent()
        self._value_accent = self._accent
        self._value_uses_base = True

        self.setObjectName("statCard")

        self.setStyleSheet(f"""
        #statCard {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        #statCard:hover {{
            border-color: {self._accent};
        }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        icon_holder = QFrame()
        icon_holder.setObjectName("statIconHolder")
        icon_holder.setFixedSize(34, 34)
        icon_holder.setStyleSheet(f"""
        background: {self._accent_rgba(0.12)};
        border-radius: 9px;
        """)
        icon_holder_layout = QVBoxLayout(icon_holder)
        icon_holder_layout.setContentsMargins(0, 0, 0, 0)
        icon_holder_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 16px; background: transparent;")
        icon_holder_layout.addWidget(icon_label)

        name_label = QLabel(title.upper())
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {TEXT_DIM}; "
            f"letter-spacing: 1px; background: transparent;"
        )

        top.addWidget(icon_holder)
        top.addWidget(name_label, 1)

        outer.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {self._value_accent}; "
            f"background: transparent;"
        )

        outer.addWidget(self.value_label)

    def _accent_rgba(self, alpha):
        color = QColor(self._accent)
        return (
            f"rgba({color.red()}, {color.green()}, "
            f"{color.blue()}, {alpha})"
        )

    def refresh_theme(self, accent=None):
        self._accent = accent or get_current_accent()
        if self._value_uses_base:
            self._value_accent = self._accent
        self.setStyleSheet(f"""
        #statCard {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        #statCard:hover {{
            border-color: {self._accent};
        }}
        """)
        self.value_label.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {self._value_accent}; "
            "background: transparent;"
        )
        # O fundo do ícone é local ao componente.
        for child in self.findChildren(QFrame):
            if child.objectName() == "statIconHolder":
                child.setStyleSheet(
                    f"background: {self._accent_rgba(0.12)}; "
                    "border-radius: 9px;"
                )

    def set_value(self, value, accent=None):

        self.value_label.setText(str(value))

        if accent:
            self._value_accent = accent
            self._value_uses_base = False
            self.value_label.setStyleSheet(
                f"font-size: 22px; font-weight: 700; color: {accent}; "
                f"background: transparent;"
            )

        self._pulse()

    def _pulse(self):
        """Pequena animação de destaque (fade) sempre que o valor muda,
        para o utilizador notar a atualização sem ser distrativo."""

        effect = QGraphicsOpacityEffect(self.value_label)
        self.value_label.setGraphicsEffect(effect)

        self._animation = QPropertyAnimation(effect, b"opacity")
        self._animation.setDuration(320)
        self._animation.setStartValue(0.25)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.start()


def page_header(title, subtitle=None):
    """Bloco de título + subtítulo consistente para o topo de cada página."""

    wrapper = QWidget()

    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    title_label = QLabel(title)
    title_label.setStyleSheet(
        f"font-size: 25px; font-weight: 700; color: {TEXT};"
    )
    layout.addWidget(title_label)

    if subtitle:

        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM};"
        )
        layout.addWidget(subtitle_label)

    return wrapper


def empty_hint(text):
    """Linha de sugestão discreta mostrada quando uma tabela está vazia."""

    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet(
        f"color: {TEXT_FAINT}; font-size: 12px; padding: 4px 2px;"
    )
    return label


class ConnectionGate(QFrame):
    """Ecrã de bloqueio mostrado em qualquer página que precise de uma
    ligação ativa ao veículo antes de fazer sentido mostrar dados —
    tal como o VCDS/Delphi nunca mostram valores sem sessão aberta."""

    goToConnection = Signal()

    def __init__(self, message=None, parent=None):

        super().__init__(parent)

        self.setObjectName("connectionGate")
        self.setStyleSheet(f"""
        #connectionGate {{
            background: {CARD_BG};
            border: 1px dashed {CARD_BORDER};
            border-radius: 14px;
        }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(40, 50, 40, 50)

        icon = QLabel("🔌")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 38px; background: transparent;")

        title = QLabel("Sem veículo ligado")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 17px; font-weight: 700; color: {TEXT}; background: transparent;"
        )

        subtitle = QLabel(
            message or "Liga-te a uma interface de diagnóstico para "
            "poderes ler dados reais do veículo aqui."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(360)
        subtitle.setStyleSheet(
            f"font-size: 13px; color: {TEXT_DIM}; background: transparent;"
        )

        button = QPushButton("⚡  Ligar ao Veículo")
        button.setObjectName("primaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(40)
        button.setMinimumWidth(200)
        button.clicked.connect(self.goToConnection.emit)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(button, 0, Qt.AlignCenter)


class SectionLabel(QLabel):
    """Cabeçalho discreto usado para agrupar itens na sidebar
    (ex.: 'DIAGNÓSTICO', 'LEITURA OBD-II', 'SISTEMA')."""

    def __init__(self, text):

        super().__init__(text.upper())

        self.setStyleSheet(f"""
        color: {TEXT_FAINT};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 14px 10px 4px 10px;
        background: transparent;
        """)


def page_with_gate(content_widget, gate_message=None):
    """Envolve o conteúdo real de uma página num QStackedWidget com um
    ConnectionGate à frente. Devolve (stack, gate) — usa
    stack.setCurrentIndex(1) quando há protocolo ligado."""

    from PySide6.QtWidgets import QStackedWidget

    stack = QStackedWidget()
    gate = ConnectionGate(gate_message)

    stack.addWidget(gate)
    stack.addWidget(content_widget)

    return stack, gate


# ---------------------------------------------------------------------
# Componentes adicionados para Live Data / DTCs / Gráficos
# ---------------------------------------------------------------------

from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import QRectF


class CategoryTabs(QWidget):
    """Fila de botões tipo "chip" para filtrar por categoria
    (ex.: Todas / Motor / Travagem-ABS / Carroçaria / Rede)."""

    def __init__(self, categories, on_change=None, parent=None):

        super().__init__(parent)

        self.on_change = on_change
        self.buttons = {}
        self.active = categories[0]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        for category in categories:

            button = QPushButton(category)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(32)
            button.setChecked(category == self.active)
            button.setObjectName("categoryChip")
            button.clicked.connect(
                lambda _checked, c=category: self._select(c)
            )

            self.buttons[category] = button
            layout.addWidget(button)

        layout.addStretch()

    def _select(self, category):

        self.active = category

        for name, button in self.buttons.items():
            button.setChecked(name == category)

        if self.on_change:
            self.on_change(category)

    def set_counts(self, counts):
        """counts: dict categoria -> nº de itens, mostrado entre parêntesis."""

        for name, button in self.buttons.items():

            count = counts.get(name)

            if count:
                button.setText(f"{name}  ({count})")
            else:
                button.setText(name)


class SeverityBadge(QLabel):
    """Etiqueta colorida para o estado de um DTC
    (Confirmado / Pendente / Permanente)."""

    COLORS = {
        "Confirmado": DANGER,
        "Permanente": "#C77DFF",
        "Pendente": WARNING,
    }

    def __init__(self, status="Confirmado"):

        super().__init__()

        self.set_status(status)

    def set_status(self, status):

        color = self.COLORS.get(status, WARNING)

        self.setText(f"  {status}  ")
        self.setStyleSheet(f"""
        background: rgba(255, 255, 255, 0.04);
        color: {color};
        border: 1px solid {color};
        border-radius: 9px;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 4px;
        """)
        self.setAlignment(Qt.AlignCenter)


class Gauge(QFrame):
    """Mostrador circular (estilo digital dash) para um parâmetro ao
    vivo — alternativa visual à tabela no Live Data."""

    def __init__(self, name, unit, min_v=0, max_v=100, color=None, parent=None):

        super().__init__(parent)

        self.name = name
        self.unit = unit
        self.min_v = min_v if min_v is not None else 0
        self.max_v = max_v if max_v is not None else 100
        self.value = None
        self.color = QColor(color or get_current_accent())
        self.setStyleSheet(f"""
        Gauge {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

    def refresh_theme(self, accent=None):
        if accent:
            self.color = QColor(accent)
        else:
            self.color = QColor(get_current_accent())
        self.update()

    def set_value(self, value):
        if value is None:
            self.value = None
        else:
            try:
                numeric = float(value)
                self.value = numeric if math.isfinite(numeric) else None
            except (TypeError, ValueError):
                self.value = None
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height() - 34)
        margin_x = (self.width() - side) / 2
        rect = QRectF(margin_x + 10, 14, side - 20, side - 20)

        start_angle = 225 * 16
        span_angle = -270 * 16

        track_pen = QPen(QColor(CARD_BORDER))
        track_pen.setWidth(10)
        track_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, start_angle, span_angle)

        if self.value is not None:

            span = (self.max_v - self.min_v) or 1
            ratio = (self.value - self.min_v) / span
            ratio = min(max(ratio, 0), 1)

            value_pen = QPen(self.color)
            value_pen.setWidth(10)
            value_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(value_pen)
            painter.drawArc(rect, start_angle, int(span_angle * ratio))

        painter.setPen(QPen(QColor(TEXT)))
        painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
        value_text = "—" if self.value is None else f"{self.value:g}"
        painter.drawText(rect, Qt.AlignCenter, value_text)

        painter.setPen(QPen(QColor(TEXT_DIM)))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(
            QRectF(0, rect.bottom() - 6, self.width(), 18),
            Qt.AlignCenter, self.unit
        )

        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            QRectF(4, self.height() - 22, self.width() - 8, 20),
            Qt.AlignCenter, self.name
        )

        painter.end()


class LiveGraph(QFrame):
    """Gráfico de linha leve (sem dependências extra) para mostrar a
    evolução de um parâmetro ao vivo, à semelhança do VAG-Scope/TDI-Graph."""

    MAX_POINTS = 180

    def __init__(self, title="", unit="", color=None, parent=None):

        super().__init__(parent)

        self.title = title
        self.unit = unit
        self.color = QColor(color or get_current_accent())
        self.y_min = 0
        self.y_max = 100
        self.values = []

        self.setMinimumHeight(220)
        self.setStyleSheet(f"""
        LiveGraph {{
            background: {CARD_BG};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}
        """)

    def refresh_theme(self, accent=None):
        if accent:
            self.color = QColor(accent)
        else:
            self.color = QColor(get_current_accent())
        self.update()

    def set_series(self, title, unit, y_min, y_max, color=None):

        self.title = title
        self.unit = unit
        self.y_min = y_min if y_min is not None else 0
        self.y_max = y_max if y_max is not None else 100

        if color:
            self.color = QColor(color)

        self.values = []
        self.update()

    def add_value(self, value):

        if value is None:
            return

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return

        if not math.isfinite(numeric):
            return

        self.values.append(numeric)

        if len(self.values) > self.MAX_POINTS:
            self.values.pop(0)

        # auto-escala suave quando o valor sai da gama teórica
        if value > self.y_max:
            self.y_max = value * 1.1
        if value < self.y_min:
            self.y_min = value * 0.9 if value >= 0 else value * 1.1

        self.update()

    def clear_series(self):
        self.values = []
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(16, 14, -16, -14)

        # título
        painter.setPen(QPen(QColor(TEXT_DIM)))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(
            rect.adjusted(0, 0, 0, -rect.height() + 18),
            Qt.AlignLeft, self.title.upper()
        )

        chart_rect = QRectF(
            rect.left(), rect.top() + 24,
            rect.width(), rect.height() - 24
        )

        # linhas de grelha
        grid_pen = QPen(QColor(CARD_BORDER))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        for i in range(4):
            y = chart_rect.top() + (chart_rect.height() * i / 3)
            painter.drawLine(chart_rect.left(), y, chart_rect.right(), y)

        if not self.values:

            painter.setPen(QPen(QColor(TEXT_FAINT)))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(chart_rect, Qt.AlignCenter, "Sem dados ainda")
            painter.end()
            return

        span = (self.y_max - self.y_min) or 1
        step_x = chart_rect.width() / max(len(self.values) - 1, 1)

        points = []

        for index, value in enumerate(self.values):

            x = chart_rect.left() + (index * step_x)
            ratio = (value - self.y_min) / span
            ratio = min(max(ratio, 0), 1)
            y = chart_rect.bottom() - (ratio * chart_rect.height())
            points.append((x, y))

        line_pen = QPen(self.color)
        line_pen.setWidthF(2.2)
        painter.setPen(line_pen)

        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(x1, y1, x2, y2)

        # último valor em destaque
        last_x, last_y = points[-1]
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(last_x - 3, last_y - 3, 6, 6)

        current = self.values[-1]
        painter.setPen(QPen(QColor(TEXT)))
        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))
        painter.drawText(
            QRectF(chart_rect.left(), rect.top() - 2, chart_rect.width(), 20),
            Qt.AlignRight,
            f"{current:g} {self.unit}"
        )

        painter.end()
