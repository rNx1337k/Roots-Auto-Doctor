import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import APP_STYLE, BG, ACCENT, TEXT, TEXT_DIM


# ============================================================
# ROOTS AUTO DOCTOR — MODERN SPLASH SCREEN
# ============================================================

APP_VERSION = "0.2.0"


def build_splash_pixmap(progress=0, status="A iniciar o sistema...", pulse=0):

    width, height = 680, 400

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    progress = max(0, min(progress, 100))

    # --------------------------------------------------------
    # Fundo
    # --------------------------------------------------------

    painter.setPen(Qt.NoPen)

    painter.setBrush(QColor(ACCENT))
    painter.drawRect(0, 0, width, 3)

    painter.setBrush(QColor(ACCENT))
    painter.drawRect(0, 0, 4, height)

    # --------------------------------------------------------
    # Pequenos detalhes técnicos
    # --------------------------------------------------------

    painter.setPen(QColor("#202020"))

    for y in range(40, 360, 40):
        painter.drawLine(30, y, width - 30, y)

    # --------------------------------------------------------
    # LOGO ROOTS
    # --------------------------------------------------------

    painter.setPen(QColor(ACCENT))

    painter.setFont(
        QFont(
            "Segoe UI",
            48,
            QFont.Bold
        )
    )

    painter.drawText(
        60,
        105,
        "ROOTS"
    )

    # --------------------------------------------------------
    # AUTO DOCTOR
    # --------------------------------------------------------

    painter.setPen(QColor(TEXT))

    painter.setFont(
        QFont(
            "Segoe UI",
            19,
            QFont.Bold
        )
    )

    painter.drawText(
        63,
        138,
        "AUTO DOCTOR"
    )

    # --------------------------------------------------------
    # Linha de separação
    # --------------------------------------------------------

    painter.setPen(
        QColor(ACCENT)
    )

    painter.drawLine(
        63,
        158,
        430,
        158
    )

    # --------------------------------------------------------
    # Descrição
    # --------------------------------------------------------

    painter.setPen(
        QColor(TEXT_DIM)
    )

    painter.setFont(
        QFont(
            "Segoe UI",
            10
        )
    )

    painter.drawText(
        63,
        187,
        "Professional Vehicle Diagnostic Software"
    )

    # --------------------------------------------------------
    # SCANNER / DIAGNOSTIC CORE
    # --------------------------------------------------------

    center_x = 555
    center_y = 118

    # Círculo exterior
    painter.setBrush(Qt.NoBrush)

    painter.setPen(
        QColor(ACCENT)
    )

    painter.drawEllipse(
        center_x - 58,
        center_y - 58,
        116,
        116
    )

    # Segundo círculo
    painter.setPen(
        QColor("#444444")
    )

    painter.drawEllipse(
        center_x - 43,
        center_y - 43,
        86,
        86
    )

    # Terceiro círculo
    painter.setPen(
        QColor(ACCENT)
    )

    painter.drawEllipse(
        center_x - 25,
        center_y - 25,
        50,
        50
    )

    # --------------------------------------------------------
    # Scanner animado
    # --------------------------------------------------------

    scan_offset = int((pulse % 100) * 0.5)

    painter.setPen(
        QColor(ACCENT)
    )

    painter.drawLine(
        center_x - 48 + scan_offset,
        center_y - 48,
        center_x + 48 + scan_offset,
        center_y + 48
    )

    # --------------------------------------------------------
    # Centro do scanner
    # --------------------------------------------------------

    painter.setBrush(
        QColor(ACCENT)
    )

    painter.setPen(Qt.NoPen)

    painter.drawEllipse(
        center_x - 5,
        center_y - 5,
        10,
        10
    )

    # --------------------------------------------------------
    # Estado atual
    # --------------------------------------------------------

    painter.setPen(
        QColor(TEXT)
    )

    painter.setFont(
        QFont(
            "Segoe UI",
            10,
            QFont.Bold
        )
    )

    painter.drawText(
        63,
        248,
        status
    )

    # --------------------------------------------------------
    # Barra de progresso
    # --------------------------------------------------------

    bar_x = 63
    bar_y = 270
    bar_width = width - 126
    bar_height = 7

    # Fundo
    painter.setBrush(
        QColor("#242424")
    )

    painter.drawRoundedRect(
        bar_x,
        bar_y,
        bar_width,
        bar_height,
        4,
        4
    )

    # Progresso
    progress_width = int(
        bar_width * (progress / 100)
    )

    if progress_width > 0:

        painter.setBrush(
            QColor(ACCENT)
        )

        painter.drawRoundedRect(
            bar_x,
            bar_y,
            progress_width,
            bar_height,
            4,
            4
        )

    # --------------------------------------------------------
    # Percentagem
    # --------------------------------------------------------

    painter.setPen(
        QColor(TEXT)
    )

    painter.setFont(
        QFont(
            "Segoe UI",
            9,
            QFont.Bold
        )
    )

    painter.drawText(
        width - 110,
        248,
        f"{progress}%"
    )

    # --------------------------------------------------------
    # Informação inferior
    # --------------------------------------------------------

    painter.setPen(
        QColor(TEXT_DIM)
    )

    painter.setFont(
        QFont(
            "Segoe UI",
            8
        )
    )

    painter.drawText(
        63,
        320,
        "ROOTS DIAGNOSTIC ENGINE"
    )

    painter.drawText(
        63,
        340,
        "OBD  •  ECU  •  LIVE DATA  •  DIAGNOSTICS"
    )

    painter.drawText(
        width - 105,
        340,
        f"v{APP_VERSION}"
    )

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------

    indicator_y = 370

    indicators = [
        ("SYSTEM", 63),
        ("OBD", 145),
        ("ECU", 205),
        ("READY", 265)
    ]

    for label, x in indicators:

        active = (
            label == "READY"
            and progress >= 95
        )

        painter.setBrush(
            QColor(ACCENT if active else "#444444")
        )

        painter.drawEllipse(
            x,
            indicator_y - 6,
            7,
            7
        )

        painter.setPen(
            QColor(TEXT_DIM)
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                7
            )
        )

        painter.drawText(
            x + 14,
            indicator_y,
            label
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
        APP_VERSION
    )

    app.setStyleSheet(
        APP_STYLE
    )

    # --------------------------------------------------------
    # Splash inicial
    # --------------------------------------------------------

    progress = 0
    pulse = 0

    splash = QSplashScreen(
        build_splash_pixmap(
            progress,
            "A iniciar o Roots Auto Doctor...",
            pulse
        )
    )

    splash.setWindowFlag(
        Qt.FramelessWindowHint
    )

    splash.show()

    app.processEvents()

    # --------------------------------------------------------
    # Criar janela principal
    # --------------------------------------------------------

    window = MainWindow()

    # --------------------------------------------------------
    # Animação do splash
    # --------------------------------------------------------

    def update_splash():

        nonlocal progress
        nonlocal pulse

        # Aproximadamente 4,5 segundos
        progress += 1
        pulse += 3

        # ----------------------------------------------------
        # Estados
        # ----------------------------------------------------

        if progress < 15:

            status = "A iniciar o sistema..."

        elif progress < 30:

            status = "A carregar módulos OBD..."

        elif progress < 45:

            status = "A preparar motor de diagnóstico..."

        elif progress < 60:

            status = "A verificar interfaces..."

        elif progress < 75:

            status = "A preparar interface..."

        elif progress < 90:

            status = "A inicializar componentes..."

        elif progress < 100:

            status = "A finalizar inicialização..."

        else:

            status = "Sistema pronto."

        # ----------------------------------------------------
        # Atualizar splash
        # ----------------------------------------------------

        splash.setPixmap(
            build_splash_pixmap(
                progress,
                status,
                pulse
            )
        )

        app.processEvents()

        # ----------------------------------------------------
        # Final
        # ----------------------------------------------------

        if progress >= 100:

            timer.stop()

            window.show()

            splash.finish(
                window
            )

    # --------------------------------------------------------
    # Timer
    # --------------------------------------------------------

    timer = QTimer()

    timer.timeout.connect(
        update_splash
    )

    # 45 ms × 100 ≈ 4,5 segundos
    timer.start(45)

    # --------------------------------------------------------
    # Aplicação
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()