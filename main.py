import sys
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QPixmap,
    QFont,
    QColor,
    QPainter,
    QPen,
    QIcon,
)
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import (
    BG,
    TEXT,
    TEXT_DIM,
    get_current_accent,
    load_and_apply_saved_theme,
)
from app.config import APP_NAME, APP_VERSION


def build_app_icon(accent=None):
    """Cria o ícone da aplicação usando a cor de destaque actual."""

    accent = accent or get_current_accent()

    size = 128

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(BG))
    painter.drawRoundedRect(
        4,
        4,
        size - 8,
        size - 8,
        26,
        26,
    )

    pen = QPen(QColor(accent))
    pen.setWidth(4)

    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    painter.drawRoundedRect(
        4,
        4,
        size - 8,
        size - 8,
        26,
        26,
    )

    painter.setPen(QColor(accent))
    painter.setFont(
        QFont(
            "Segoe UI",
            56,
            QFont.Weight.Bold,
        )
    )

    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        "R",
    )

    painter.end()

    return QIcon(pixmap)


def build_splash_pixmap(animation=0, accent=None):
    """Cria o Splash usando o tema actualmente seleccionado."""

    accent = accent or get_current_accent()

    width = 560
    height = 320

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    accent_color = QColor(accent)
    text = QColor(TEXT)
    text_dim = QColor(TEXT_DIM)

    # ========================================================
    # TOPO — pequena linha de destaque
    # ========================================================

    painter.setPen(Qt.NoPen)
    painter.setBrush(accent_color)

    painter.drawRoundedRect(
        width // 2 - 22,
        28,
        44,
        3,
        1.5,
        1.5,
    )

    # ========================================================
    # LOGO / NOME
    # ========================================================

    painter.setPen(accent_color)
    painter.setFont(
        QFont(
            "Segoe UI",
            38,
            QFont.Weight.Bold,
        )
    )

    painter.drawText(
        0,
        92,
        width,
        50,
        Qt.AlignCenter,
        "ROOTS",
    )

    # ========================================================
    # SUBTÍTULO
    # ========================================================

    painter.setPen(text)
    painter.setFont(
        QFont(
            "Segoe UI",
            13,
            QFont.Weight.DemiBold,
        )
    )

    painter.drawText(
        0,
        132,
        width,
        30,
        Qt.AlignCenter,
        "AUTO DOCTOR",
    )

    # ========================================================
    # DESCRIÇÃO
    # ========================================================

    painter.setPen(text_dim)
    painter.setFont(
        QFont(
            "Segoe UI",
            9,
        )
    )

    painter.drawText(
        0,
        170,
        width,
        25,
        Qt.AlignCenter,
        "A preparar o sistema...",
    )

    # ========================================================
    # LOADER MODERNO
    # ========================================================

    center_x = width // 2
    center_y = 218

    outer_radius = 13

    for i in range(12):
        angle = animation + (i * 30)

        radians = math.radians(angle)

        x = center_x + math.cos(radians) * outer_radius
        y = center_y + math.sin(radians) * outer_radius

        opacity = int(35 + (220 * (i + 1) / 12))

        color = QColor(accent_color)
        color.setAlpha(opacity)

        painter.setPen(Qt.NoPen)
        painter.setBrush(color)

        dot_size = 3 if i < 8 else 2

        painter.drawEllipse(
            int(x - dot_size / 2),
            int(y - dot_size / 2),
            dot_size,
            dot_size,
        )

    # Pequeno ponto central
    center_color = QColor(accent_color)
    center_color.setAlpha(180)

    painter.setBrush(center_color)

    painter.drawEllipse(
        center_x - 2,
        center_y - 2,
        4,
        4,
    )

    # ========================================================
    # VERSÃO
    # ========================================================

    painter.setPen(text_dim)
    painter.setFont(
        QFont(
            "Segoe UI",
            8,
        )
    )

    painter.drawText(
        0,
        282,
        width,
        20,
        Qt.AlignCenter,
        f"v{APP_VERSION}",
    )

    painter.end()

    return pixmap


def main():

    app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # ========================================================
    # CARREGAR TEMA GUARDADO
    # ========================================================
    #
    # IMPORTANTE:
    # O tema é aplicado antes de criar o Splash.
    # Assim, Splash + aplicação começam com exactamente
    # a mesma cor.
    #
    load_and_apply_saved_theme(app)

    accent = get_current_accent()

    # ========================================================
    # ÍCONE DA APLICAÇÃO
    # ========================================================

    app_icon = build_app_icon(accent)
    app.setWindowIcon(app_icon)

    # ========================================================
    # SPLASH SCREEN
    # ========================================================

    animation = 0

    splash = QSplashScreen(
        build_splash_pixmap(
            animation,
            accent,
        ),
        Qt.WindowStaysOnTopHint,
    )

    splash.setWindowFlag(
        Qt.FramelessWindowHint
    )

    splash.show()

    app.processEvents()

    # ========================================================
    # ANIMAÇÃO
    # ========================================================

    def update_splash():

        nonlocal animation

        animation = (animation + 30) % 360

        splash.setPixmap(
            build_splash_pixmap(
                animation,
                accent,
            )
        )

        app.processEvents()

    loader_timer = QTimer()
    loader_timer.timeout.connect(update_splash)
    loader_timer.start(100)

    # ========================================================
    # ABRIR APLICAÇÃO
    # ========================================================

    def start_application():

        loader_timer.stop()

        window = MainWindow()
        window.setWindowIcon(app_icon)
        window.show()

        splash.finish(window)

    QTimer.singleShot(
        1500,
        start_application,
    )

    # ========================================================
    # START
    # ========================================================

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

