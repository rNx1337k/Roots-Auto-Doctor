"""
Conversão de unidades de apresentação (temperatura, pressão) de
acordo com a preferência do utilizador, guardada em Sistema >
Preferências.

Importante: os valores internos, os PIDs e o protocolo OBD-II
continuam sempre nas unidades standard SAE (°C, kPa) — a conversão
acontece só na camada de apresentação (tabelas, mostradores,
gráficos, freeze frame), nunca nos dados lidos da ECU.
"""

from PySide6.QtCore import QSettings

from app.config import SETTINGS_ORGANISATION, SETTINGS_APPLICATION

TEMPERATURE_KEY = "preferences/temperature_unit"
PRESSURE_KEY = "preferences/pressure_unit"


def _settings():
    return QSettings(SETTINGS_ORGANISATION, SETTINGS_APPLICATION)


def temperature_unit():
    """Unidade de temperatura preferida pelo utilizador ('°C' ou '°F')."""

    return _settings().value(TEMPERATURE_KEY, "°C")


def pressure_unit():
    """Unidade de pressão preferida pelo utilizador
    ('bar', 'PSI' ou 'kPa')."""

    return _settings().value(PRESSURE_KEY, "bar")


def preferred_unit(base_unit):
    """Dada a unidade standard SAE de um PID, devolve a unidade em
    que deve ser apresentado ao utilizador. Unidades sem preferência
    associada (rpm, km/h, %, V...) são devolvidas sem alteração."""

    if base_unit == "°C":
        return temperature_unit()

    if base_unit == "kPa":
        return pressure_unit()

    return base_unit


def convert_value(value, from_unit, to_unit):
    """Converte um valor numérico entre unidades. Se a conversão não
    for reconhecida, devolve o valor original sem alterações."""

    if value is None or not isinstance(value, (int, float)):
        return value

    if from_unit == to_unit:
        return value

    if from_unit == "°C" and to_unit == "°F":
        return round(value * 9 / 5 + 32, 1)

    if from_unit == "kPa" and to_unit == "bar":
        return round(value / 100, 3)

    if from_unit == "kPa" and to_unit == "PSI":
        return round(value * 0.1450377, 1)

    return value


def convert_for_display(value, unit):
    """Converte um par (valor, unidade) em bruto — tal como vem do
    protocolo OBD-II — para a unidade preferida pelo utilizador.
    Devolve sempre (valor, unidade), convertidos ou não."""

    target = preferred_unit(unit)

    return convert_value(value, unit, target), target


def convert_range(min_v, max_v, unit):
    """Converte também os limites de uma gama (min/max), usados para
    escalar mostradores e gráficos, mantendo-os coerentes com o
    valor convertido por convert_for_display."""

    target = preferred_unit(unit)

    new_min = convert_value(min_v, unit, target)
    new_max = convert_value(max_v, unit, target)

    return new_min, new_max, target
