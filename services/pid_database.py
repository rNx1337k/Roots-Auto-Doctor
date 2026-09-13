"""
Tabela de PIDs standard do Modo 01 (dados em tempo real), conforme a
norma SAE J1979 / ISO 15031-5. Estes PIDs e fórmulas são o standard
público usado por qualquer scanner OBD-II genérico.

Cada entrada:
    pid       -> número do PID (Modo 01)
    name      -> nome apresentado ao utilizador
    category  -> agrupamento usado nos filtros da UI
    unit      -> unidade apresentada
    bytes     -> nº de bytes de dados esperados na resposta
    decode    -> função(bytes) -> valor numérico/str já convertido
    min / max -> gama teórica (usada para escalar gráficos)
"""

CATEGORY_ENGINE = "Motor"
CATEGORY_FUEL = "Combustível"
CATEGORY_EMISSIONS = "Emissões"
CATEGORY_INTAKE = "Admissão"
CATEGORY_ELECTRICAL = "Elétrico"
CATEGORY_VEHICLE = "Veículo"

ALL_CATEGORIES = [
    CATEGORY_ENGINE,
    CATEGORY_FUEL,
    CATEGORY_INTAKE,
    CATEGORY_EMISSIONS,
    CATEGORY_ELECTRICAL,
    CATEGORY_VEHICLE,
]


def _a(b):
    return b[0]


def _percent(b):
    return round(b[0] * 100 / 255, 1)


def _temp(b):
    return b[0] - 40


def _rpm(b):
    return round(((b[0] * 256) + b[1]) / 4, 0)


def _speed(b):
    return b[0]


def _timing_advance(b):
    return round((b[0] / 2) - 64, 1)


def _maf(b):
    return round(((b[0] * 256) + b[1]) / 100, 2)


def _fuel_trim(b):
    return round((b[0] - 128) * 100 / 128, 1)


def _o2_voltage(b):
    return round(b[0] / 200, 3)


def _pressure_kpa(b):
    return b[0]


def _pressure_2byte_kpa(b):
    return ((b[0] * 256) + b[1]) * 10


def _runtime_seconds(b):
    return (b[0] * 256) + b[1]


def _distance_km(b):
    return (b[0] * 256) + b[1]


def _voltage_module(b):
    return round(((b[0] * 256) + b[1]) / 1000, 2)


PID_TABLE = [
    {"pid": 0x04, "name": "Carga do motor (calculada)", "category": CATEGORY_ENGINE,
     "unit": "%", "bytes": 1, "decode": _percent, "min": 0, "max": 100},

    {"pid": 0x05, "name": "Temperatura do líquido de refrigeração", "category": CATEGORY_ENGINE,
     "unit": "°C", "bytes": 1, "decode": _temp, "min": -40, "max": 150},

    {"pid": 0x06, "name": "Fuel Trim curto prazo (Banco 1)", "category": CATEGORY_FUEL,
     "unit": "%", "bytes": 1, "decode": _fuel_trim, "min": -100, "max": 100},

    {"pid": 0x07, "name": "Fuel Trim longo prazo (Banco 1)", "category": CATEGORY_FUEL,
     "unit": "%", "bytes": 1, "decode": _fuel_trim, "min": -100, "max": 100},

    {"pid": 0x08, "name": "Fuel Trim curto prazo (Banco 2)", "category": CATEGORY_FUEL,
     "unit": "%", "bytes": 1, "decode": _fuel_trim, "min": -100, "max": 100},

    {"pid": 0x09, "name": "Fuel Trim longo prazo (Banco 2)", "category": CATEGORY_FUEL,
     "unit": "%", "bytes": 1, "decode": _fuel_trim, "min": -100, "max": 100},

    {"pid": 0x0A, "name": "Pressão de combustível", "category": CATEGORY_FUEL,
     "unit": "kPa", "bytes": 1, "decode": lambda b: b[0] * 3, "min": 0, "max": 765},

    {"pid": 0x0B, "name": "Pressão absoluta no coletor de admissão", "category": CATEGORY_INTAKE,
     "unit": "kPa", "bytes": 1, "decode": _pressure_kpa, "min": 0, "max": 255},

    {"pid": 0x0C, "name": "Rotação do motor (RPM)", "category": CATEGORY_ENGINE,
     "unit": "rpm", "bytes": 2, "decode": _rpm, "min": 0, "max": 8000},

    {"pid": 0x0D, "name": "Velocidade do veículo", "category": CATEGORY_VEHICLE,
     "unit": "km/h", "bytes": 1, "decode": _speed, "min": 0, "max": 255},

    {"pid": 0x0E, "name": "Avanço da ignição", "category": CATEGORY_ENGINE,
     "unit": "°", "bytes": 1, "decode": _timing_advance, "min": -64, "max": 63.5},

    {"pid": 0x0F, "name": "Temperatura do ar de admissão", "category": CATEGORY_INTAKE,
     "unit": "°C", "bytes": 1, "decode": _temp, "min": -40, "max": 215},

    {"pid": 0x10, "name": "Caudal de ar (MAF)", "category": CATEGORY_INTAKE,
     "unit": "g/s", "bytes": 2, "decode": _maf, "min": 0, "max": 655},

    {"pid": 0x11, "name": "Posição da borboleta (acelerador)", "category": CATEGORY_ENGINE,
     "unit": "%", "bytes": 1, "decode": _percent, "min": 0, "max": 100},

    {"pid": 0x1F, "name": "Tempo desde o arranque do motor", "category": CATEGORY_ENGINE,
     "unit": "s", "bytes": 2, "decode": _runtime_seconds, "min": 0, "max": 65535},

    {"pid": 0x21, "name": "Distância percorrida com avaria (MIL) ativa", "category": CATEGORY_EMISSIONS,
     "unit": "km", "bytes": 2, "decode": _distance_km, "min": 0, "max": 65535},

    {"pid": 0x2F, "name": "Nível de combustível", "category": CATEGORY_FUEL,
     "unit": "%", "bytes": 1, "decode": _percent, "min": 0, "max": 100},

    {"pid": 0x31, "name": "Distância desde a limpeza de códigos", "category": CATEGORY_EMISSIONS,
     "unit": "km", "bytes": 2, "decode": _distance_km, "min": 0, "max": 65535},

    {"pid": 0x33, "name": "Pressão barométrica", "category": CATEGORY_INTAKE,
     "unit": "kPa", "bytes": 1, "decode": _pressure_kpa, "min": 0, "max": 255},

    {"pid": 0x42, "name": "Tensão da bateria / módulo de controlo", "category": CATEGORY_ELECTRICAL,
     "unit": "V", "bytes": 2, "decode": _voltage_module, "min": 0, "max": 65.5},

    {"pid": 0x43, "name": "Carga absoluta do motor", "category": CATEGORY_ENGINE,
     "unit": "%", "bytes": 2, "decode": lambda b: round(((b[0] * 256) + b[1]) * 100 / 255, 1),
     "min": 0, "max": 25700},

    {"pid": 0x45, "name": "Posição relativa da borboleta", "category": CATEGORY_ENGINE,
     "unit": "%", "bytes": 1, "decode": _percent, "min": 0, "max": 100},

    {"pid": 0x46, "name": "Temperatura ambiente", "category": CATEGORY_VEHICLE,
     "unit": "°C", "bytes": 1, "decode": _temp, "min": -40, "max": 215},

    {"pid": 0x5C, "name": "Temperatura do óleo do motor", "category": CATEGORY_ENGINE,
     "unit": "°C", "bytes": 1, "decode": _temp, "min": -40, "max": 210},
]

PID_INDEX = {entry["pid"]: entry for entry in PID_TABLE}


def get_pid(pid):
    return PID_INDEX.get(pid)


def pids_by_category(category=None):

    if not category or category == "Todas":
        return list(PID_TABLE)

    return [entry for entry in PID_TABLE if entry["category"] == category]


def search_pids(term):

    term = (term or "").strip().lower()

    if not term:
        return list(PID_TABLE)

    return [
        entry for entry in PID_TABLE
        if term in entry["name"].lower()
    ]
