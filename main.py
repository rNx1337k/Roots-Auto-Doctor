import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import APP_STYLE, BG, ACCENT, TEXT, TEXT_DIM


APP_VERSION = "0.2.0"


def build_splash_pixmap(animation=0):
    width = 500
    height = 300

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    accent = QColor(ACCENT)
    text = QColor(TEXT)
    text_dim = QColor(TEXT_DIM)

    # Linha superior
    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)
    painter.drawRect(0, 0, width, 3)

    # ROOTS
    painter.setPen(accent)
    painter.setFont(QFont("Segoe UI", 38, QFont.Bold))

    painter.drawText(
        0,
        85,
        width,
        50,
        Qt.AlignCenter,
        "ROOTS"
    )

    # AUTO DOCTOR
    painter.setPen(text)
    painter.setFont(QFont("Segoe UI", 15, QFont.Bold))

    painter.drawText(
        0,
        115,
        width,
        35,
        Qt.AlignCenter,
        "AUTO DOCTOR"
    )

    # Mensagem
    painter.setPen(text_dim)
    painter.setFont(QFont("Segoe UI", 9))

    painter.drawText(
        0,
        165,
        width,
        30,
        Qt.AlignCenter,
        "A iniciar o sistema..."
    )

    # Loader
    center_x = width // 2
    center_y = 220
    radius = 20

    for i in range(12):
        angle = (animation + i * 30) % 360

        opacity = int(255 * (i + 1) / 12)

        color = QColor(accent)
        color.setAlpha(opacity)

        pen = QPen(color)
        pen.setWidth(4)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        # Coordenadas do ponto do loader
        import math

        radians = math.radians(angle)

        x1 = center_x + int(math.cos(radians) * 10)
        y1 = center_y + int(math.sin(radians) * 10)

        x2 = center_x + int(math.cos(radians) * radius)
        y2 = center_y + int(math.sin(radians) * radius)

        painter.drawLine(x1, y1, x2, y2)

    # Versão
    painter.setPen(text_dim)
    painter.setFont(QFont("Segoe UI", 8))

    painter.drawText(
        0,
        270,
        width,
        20,
        Qt.AlignCenter,
        f"v{APP_VERSION}"
    )

    painter.end()

    return pixmap


def main():

    app = QApplication(sys.argv)

    app.setApplicationName("Roots Auto Doctor")
    app.setApplicationVersion(APP_VERSION)

    app.setStyleSheet(APP_STYLE)

    # ========================================================
    # SPLASH
    # ========================================================

    animation = 0

    splash = QSplashScreen(
        build_splash_pixmap(animation),
        Qt.WindowStaysOnTopHint
    )

    splash.setWindowFlag(Qt.FramelessWindowHint)

    splash.show()

    app.processEvents()

    # ========================================================
    # LOADER
    # ========================================================

    def update_splash():

        nonlocal animation

        animation = (animation + 30) % 360

        splash.setPixmap(
            build_splash_pixmap(animation)
        )

        app.processEvents()

    # ========================================================
    # TIMER DO LOADER
    # ========================================================

    loader_timer = QTimer()
    loader_timer.timeout.connect(update_splash)
    loader_timer.start(100)

    # ========================================================
    # ABRIR A APLICAÇÃO
    # ========================================================

    def start_application():

        loader_timer.stop()

        window = MainWindow()
        window.show()

        splash.finish(window)

    # Aguarda aproximadamente 1.5 segundos
    QTimer.singleShot(1500, start_application)

    # ========================================================
    # START
    # ========================================================

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
