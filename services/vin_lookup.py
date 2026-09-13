"""
Estimativa do fabricante a partir do WMI (World Manufacturer
Identifier — os 3 primeiros carateres do VIN). É informação pública
e standard (ISO 3780), mas fica sempre marcada como "estimativa",
porque um mesmo WMI pode ser partilhado entre marcas de um grupo.
"""

WMI_TABLE = {
    "WVW": "Volkswagen", "WV1": "Volkswagen", "WV2": "Volkswagen",
    "WAU": "Audi", "WA1": "Audi",
    "WBA": "BMW", "WBS": "BMW M", "WBY": "BMW",
    "WDB": "Mercedes-Benz", "WDD": "Mercedes-Benz", "WDC": "Mercedes-Benz",
    "WF0": "Ford", "WFO": "Ford",
    "VF1": "Renault", "VF3": "Peugeot", "VF7": "Citroën", "VF8": "Peugeot",
    "TMB": "Škoda", "TMK": "Škoda",
    "VSS": "SEAT",
    "ZFA": "Fiat", "ZFF": "Ferrari",
    "SAL": "Land Rover", "SAJ": "Jaguar",
    "YV1": "Volvo", "YV4": "Volvo",
    "JHM": "Honda", "JH4": "Acura",
    "JT2": "Toyota", "JTD": "Toyota", "JTN": "Toyota",
    "JN1": "Nissan", "JN8": "Nissan",
    "1FA": "Ford", "1FT": "Ford", "1G1": "Chevrolet", "1G6": "Cadillac",
    "1HG": "Honda", "2HG": "Honda", "1N4": "Nissan",
    "KMH": "Hyundai", "KNA": "Kia",
    "KL1": "Chevrolet (Coreia)",
}


def guess_make(vin):

    if not vin or len(vin) < 3:
        return None

    return WMI_TABLE.get(vin[:3].upper())
