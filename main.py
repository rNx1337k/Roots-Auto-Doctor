import sys
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow
from gui.styles import APP_STYLE, BG, ACCENT, TEXT, TEXT_DIM


# ============================================================
# ROOTS AUTO DOCTOR — PREMIUM SPLASH SCREEN
# ============================================================

APP_VERSION = "0.2.0"


def build_splash_pixmap(
    progress=0,
    status="A iniciar o sistema...",
    animation=0
):
    width = 720
    height = 420

    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(BG))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    progress = max(0, min(progress, 100))

    # ========================================================
    # CORES
    # ========================================================

    accent = QColor(ACCENT)
    text = QColor(TEXT)
    text_dim = QColor(TEXT_DIM)

    dark_line = QColor("#202020")
    dark_panel = QColor("#181818")
    dark_bar = QColor("#252525")

    # ========================================================
    # FUNDO
    # ========================================================

    painter.fillRect(
        0,
        0,
        width,
        height,
        QColor(BG)
    )

    # Linha superior
    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)

    painter.drawRect(
        0,
        0,
        width,
        3
    )

    # Linha lateral
    painter.drawRect(
        0,
        0,
        3,
        height
    )

    # ========================================================
    # GRELHA TÉCNICA DISCRETA
    # ========================================================

    grid_pen = QPen(dark_line)
    grid_pen.setWidth(1)

    painter.setPen(grid_pen)

    for x in range(40, width, 40):
        painter.drawLine(
            x,
            20,
            x,
            height - 20
        )

    for y in range(40, height, 40):
        painter.drawLine(
            20,
            y,
            width - 20,
            y
        )

    # ========================================================
    # CABEÇALHO / BRANDING
    # ========================================================

    painter.setPen(accent)

    painter.setFont(
        QFont(
            "Segoe UI",
            46,
            QFont.Bold
        )
    )

    painter.drawText(
        55,
        105,
        "ROOTS"
    )

    painter.setPen(text)

    painter.setFont(
        QFont(
            "Segoe UI",
            18,
            QFont.Bold
        )
    )

    painter.drawText(
        58,
        135,
        "AUTO DOCTOR"
    )

    # Linha de branding
    painter.setPen(accent)

    painter.drawLine(
        58,
        153,
        390,
        153
    )

    # Descrição
    painter.setPen(text_dim)

    painter.setFont(
        QFont(
            "Segoe UI",
            10
        )
    )

    painter.drawText(
        58,
        180,
        "Professional Vehicle Diagnostic Software"
    )

    # ========================================================
    # PAINEL DO SCANNER
    # ========================================================

    scanner_x = 560
    scanner_y = 120

    painter.setPen(Qt.NoPen)
    painter.setBrush(dark_panel)

    painter.drawEllipse(
        scanner_x - 78,
        scanner_y - 78,
        156,
        156
    )

    # ========================================================
    # ANÉIS DO SCANNER
    # ========================================================

    # Anel exterior
    outer_pen = QPen(accent)
    outer_pen.setWidth(2)

    painter.setPen(outer_pen)
    painter.setBrush(Qt.NoBrush)

    painter.drawEllipse(
        scanner_x - 65,
        scanner_y - 65,
        130,
        130
    )

    # Anel intermédio
    middle_pen = QPen(QColor("#444444"))
    middle_pen.setWidth(1)

    painter.setPen(middle_pen)

    painter.drawEllipse(
        scanner_x - 48,
        scanner_y - 48,
        96,
        96
    )

    # Anel interior
    inner_pen = QPen(accent)
    inner_pen.setWidth(1)

    painter.setPen(inner_pen)

    painter.drawEllipse(
        scanner_x - 30,
        scanner_y - 30,
        60,
        60
    )

    # ========================================================
    # MARCAS DO SCANNER
    # ========================================================

    mark_pen = QPen(accent)
    mark_pen.setWidth(2)

    painter.setPen(mark_pen)

    for angle in range(0, 360, 45):

        radians = math.radians(angle)

        x1 = scanner_x + math.cos(radians) * 68
        y1 = scanner_y + math.sin(radians) * 68

        x2 = scanner_x + math.cos(radians) * 75
        y2 = scanner_y + math.sin(radians) * 75

        painter.drawLine(
            int(x1),
            int(y1),
            int(x2),
            int(y2)
        )

    # ========================================================
    # SCANNER ANIMADO
    # ========================================================

    angle = animation % 360
    radians = math.radians(angle)

    scan_x = scanner_x + math.cos(radians) * 52
    scan_y = scanner_y + math.sin(radians) * 52

    scan_pen = QPen(accent)
    scan_pen.setWidth(2)

    painter.setPen(scan_pen)

    painter.drawLine(
        scanner_x,
        scanner_y,
        int(scan_x),
        int(scan_y)
    )

    # Ponto central
    painter.setPen(Qt.NoPen)
    painter.setBrush(accent)

    painter.drawEllipse(
        scanner_x - 5,
        scanner_y - 5,
        10,
        10
    )

    # ========================================================
    # ESTADO DO SISTEMA
    # ========================================================

    painter.setPen(text)

    painter.setFont(
        QFont(
            "Segoe UI",
            10,
            QFont.Bold
        )
    )

    painter.drawText(
        58,
        238,
        status
    )

    # ========================================================
    # PERCENTAGEM
    # ========================================================

    painter.setPen(accent)

    painter.setFont(
        QFont(
            "Segoe UI",
            11,
            QFont.Bold
        )
    )

    painter.drawText(
        width - 105,
        238,
        f"{progress:03d}%"
    )

    # ========================================================
    # BARRA DE PROGRESSO
    # ========================================================

    bar_x = 58
    bar_y = 258
    bar_width = width - 116
    bar_height = 8

    painter.setPen(Qt.NoPen)

    painter.setBrush(dark_bar)

    painter.drawRoundedRect(
        bar_x,
        bar_y,
        bar_width,
        bar_height,
        4,
        4
    )

    progress_width = int(
        bar_width * progress / 100
    )

    if progress_width > 0:

        painter.setBrush(accent)

        painter.drawRoundedRect(
            bar_x,
            bar_y,
            progress_width,
            bar_height,
            4,
            4
        )

    # ========================================================
    # INFORMAÇÃO TÉCNICA
    # ========================================================

    painter.setPen(text_dim)

    painter.setFont(
        QFont(
            "Segoe UI",
            8
        )
    )

    painter.drawText(
        58,
        305,
        "ROOTS DIAGNOSTIC ENGINE"
    )

    painter.drawText(
        58,
        323,
        "OBD  •  ECU  •  LIVE DATA  •  FAULT DIAGNOSTICS"
    )

    painter.drawText(
        width - 105,
        323,
        f"v{APP_VERSION}"
    )

    # ========================================================
    # INDICADORES DO SISTEMA
    # ========================================================

    indicators = [
        ("SYSTEM", 58, 35),
        ("OBD", 165, 50),
        ("ECU", 250, 65),
        ("ENGINE", 340, 80),
        ("READY", 470, 95),
    ]

    indicator_y = 370

    for label, x, required_progress:

        active = progress >= required_progress

        if active:
            dot_color = accent
            label_color = text
        else:
            dot_color = QColor("#3A3A3A")
            label_color = text_dim

        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)

        painter.drawEllipse(
            x,
            indicator_y - 5,
            8,
            8
        )

        painter.setPen(label_color)

        painter.setFont(
            QFont(
                "Segoe UI",
                7,
                QFont.Bold
            )
        )

        painter.drawText(
            x + 16,
            indicator_y + 2,
            label
        )

    # ========================================================
    # STATUS FINAL
    # ========================================================

    if progress >= 100:

        painter.setPen(accent)

        painter.setFont(
            QFont(
                "Segoe UI",
                8,
                QFont.Bold
            )
        )

        painter.drawText(
            width - 155,
            370,
            "DIAGNOSTIC READY"
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

    # ========================================================
    # SPLASH
    # ========================================================

    progress = 0
    animation = 0

    splash = QSplashScreen(
        build_splash_pixmap(
            0,
            "A iniciar o Roots Auto Doctor...",
            0
        )
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

        nonlocal progress
        nonlocal animation

        progress += 1
        animation = (animation + 6) % 360

        # ----------------------------------------------------
        # Mensagens
        # ----------------------------------------------------

        if progress < 12:

            status = "A iniciar o sistema..."

        elif progress < 25:

            status = "A carregar módulos OBD..."

        elif progress < 40:

            status = "A preparar motor de diagnóstico..."

        elif progress < 55:

            status = "A verificar interfaces..."

        elif progress < 70:

            status = "A carregar componentes ECU..."

        elif progress < 85:

            status = "A preparar Live Data..."

        elif progress < 96:

            status = "A verificar sistema..."

        else:

            status = "Sistema pronto."

        # ----------------------------------------------------
        # Atualizar imagem
        # ----------------------------------------------------

        splash.setPixmap(
            build_splash_pixmap(
                progress,
                status,
                animation
            )
        )

        app.processEvents()

        # ----------------------------------------------------
        # Final
        # ----------------------------------------------------

        if progress >= 100:

            timer.stop()

            window = MainWindow()

            window.show()

            splash.finish(
                window
            )

    # ========================================================
    # TIMER
    # ========================================================

    timer = QTimer()

    timer.timeout.connect(
        update_splash
    )

    # 50 ms × 100 passos = aproximadamente 5 segundos
    timer.start(50)

    # ========================================================
    # START
    # ========================================================

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()