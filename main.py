```python
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import APP_STYLE, BG, ACCENT, TEXT, TEXT_DIM


# ============================================================
# ROOTS AUTO DOCTOR — SPLASH SCREEN
# ============================================================

def build_splash_pixmap(progress=0, status="A iniciar o sistema..."):

    width, height = 620, 360

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # --------------------------------------------------------
    # Fundo / detalhes
    # --------------------------------------------------------

    painter.setPen(Qt.NoPen)

    # Linha decorativa superior
    painter.setBrush(QColor(ACCENT))
    painter.drawRect(0, 0, width, 3)

    # Pequeno detalhe lateral
    painter.setBrush(QColor(ACCENT))
    painter.drawRect(0, 0, 4, height)

    # --------------------------------------------------------
    # ROOTS
    # --------------------------------------------------------

    painter.setPen(QColor(ACCENT))
    painter.setFont(
        QFont("Segoe UI", 42, QFont.Bold)
    )

    painter.drawText(
        55,
        105,
        "ROOTS"
    )

    # --------------------------------------------------------
    # AUTO DOCTOR
    # --------------------------------------------------------

    painter.setPen(QColor(TEXT))
    painter.setFont(
        QFont("Segoe UI", 18, QFont.Bold)
    )

    painter.drawText(
        58,
        138,
        "AUTO DOCTOR"
    )

    # --------------------------------------------------------
    # Linha
    # --------------------------------------------------------

    painter.setPen(QColor(ACCENT))
    painter.drawLine(
        58,
        158,
        width - 58,
        158
    )

    # --------------------------------------------------------
    # Descrição
    # --------------------------------------------------------

    painter.setPen(QColor(TEXT_DIM))
    painter.setFont(
        QFont("Segoe UI", 10)
    )

    painter.drawText(
        58,
        190,
        "Professional Vehicle Diagnostic Software"
    )

    # --------------------------------------------------------
    # Estado
    # --------------------------------------------------------

    painter.setPen(QColor(TEXT))
    painter.setFont(
        QFont("Segoe UI", 10, QFont.Bold)
    )

    painter.drawText(
        58,
        245,
        status
    )

    # --------------------------------------------------------
    # Barra de progresso
    # --------------------------------------------------------

    bar_x = 58
    bar_y = 265
    bar_width = width - 116
    bar_height = 6

    # Fundo da barra
    painter.setBrush(QColor("#252525"))
    painter.setPen(Qt.NoPen)

    painter.drawRoundedRect(
        bar_x,
        bar_y,
        bar_width,
        bar_height,
        3,
        3
    )

    # Progresso
    progress = max(0, min(progress, 100))

    progress_width = int(
        bar_width * (progress / 100)
    )

    if progress_width > 0:

        painter.setBrush(QColor(ACCENT))

        painter.drawRoundedRect(
            bar_x,
            bar_y,
            progress_width,
            bar_height,
            3,
            3
        )

    # --------------------------------------------------------
    # Informação inferior
    # --------------------------------------------------------

    painter.setPen(QColor(TEXT_DIM))
    painter.setFont(
        QFont("Segoe UI", 8)
    )

    painter.drawText(
        58,
        305,
        f"System initialization  •  {progress}%"
    )

    painter.drawText(
        width - 115,
        305,
        "v0.3.0"
    )

    # --------------------------------------------------------
    # Indicador de diagnóstico
    # --------------------------------------------------------

    center_x = width - 105
    center_y = 115

    painter.setPen(
        QColor(ACCENT)
    )

    painter.setBrush(Qt.NoBrush)

    painter.drawEllipse(
        center_x - 32,
        center_y - 32,
        64,
        64
    )

    painter.drawEllipse(
        center_x - 20,
        center_y - 20,
        40,
        40
    )

    painter.setPen(QColor(TEXT))
    painter.drawLine(
        center_x,
        center_y - 20,
        center_x,
        center_y + 20
    )

    painter.drawLine(
        center_x - 20,
        center_y,
        center_x + 20,
        center_y
    )

    painter.end()

    return pixmap


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Roots Auto Doctor"
    )

    app.setApplicationVersion(
        "0.3.0"
    )

    app.setStyleSheet(
        APP_STYLE
    )

    # --------------------------------------------------------
    # Splash
    # --------------------------------------------------------

    splash = QSplashScreen(
        build_splash_pixmap(
            0,
            "A iniciar o Roots Auto Doctor..."
        )
    )

    splash.setWindowFlag(
        Qt.FramelessWindowHint
    )

    splash.show()

    app.processEvents()

    # --------------------------------------------------------
    # Criar aplicação principal
    # --------------------------------------------------------

    window = MainWindow()

    # --------------------------------------------------------
    # Animação
    # --------------------------------------------------------

    progress = 0

    def update_splash():

        nonlocal progress

        progress += 4

        if progress < 25:

            status = "A carregar módulos..."

        elif progress < 50:

            status = "A preparar interface..."

        elif progress < 75:

            status = "A inicializar sistema de diagnóstico..."

        elif progress < 95:

            status = "A verificar componentes..."

        else:

            status = "Sistema pronto."

        splash.setPixmap(
            build_splash_pixmap(
                progress,
                status
            )
        )

        app.processEvents()

        if progress >= 100:

            timer.stop()

            window.show()

            splash.finish(
                window
            )

    timer = QTimer()

    timer.timeout.connect(
        update_splash
    )

    timer.start(30)

    # --------------------------------------------------------
    # Iniciar aplicação
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
