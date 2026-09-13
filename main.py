import sys
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QPixmap,
    QFont,
    QColor,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import APP_STYLE, BG, ACCENT, TEXT, TEXT_DIM


APP_VERSION = "0.2.0"


def build_splash_pixmap(animation=0):
    width = 560
    height = 320

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    accent = QColor(ACCENT)
    text = QColor(TEXT)
    text_dim = QColor(TEXT_DIM)

    # ========================================================
    # TOPO — pequena linha de destaque
    # ========================================================

    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)

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

    painter.setPen(accent)
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
    inner_radius = 8

    for i in range(12):
        angle = animation + (i * 30)

        radians = math.radians(angle)

        # Fazemos os pontos ficarem em círculo
        x = center_x + math.cos(radians) * outer_radius
        y = center_y + math.sin(radians) * outer_radius

        # O ponto mais recente é mais forte
        opacity = int(35 + (220 * (i + 1) / 12))

        color = QColor(accent)
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
    center_color = QColor(accent)
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

    app.setApplicationName("Roots Auto Doctor")
    app.setApplicationVersion(APP_VERSION)

    app.setStyleSheet(APP_STYLE)

    # ========================================================
    # SPLASH SCREEN
    # ========================================================

    animation = 0

    splash = QSplashScreen(
        build_splash_pixmap(animation),
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
            build_splash_pixmap(animation)
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
