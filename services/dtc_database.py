"""
Descodificação e catalogação de códigos de falha (DTC).

A conversão dos 2 bytes devolvidos pelo Modo 03/07 num código do tipo
"P0301" segue a norma SAE J2012 / ISO 15031-6 — é o mesmo algoritmo
standard usado por qualquer scanner OBD-II genérico (VCDS, Torque,
Autel, etc. para a parte genérica dos códigos).

As descrições incluídas cobrem os códigos genéricos (SAE) mais comuns.
Códigos específicos de fabricante (ex.: P1xxx de uma marca em concreto)
não têm descrição pública fiável e são devolvidos apenas com a
categoria + aviso "específico do fabricante".
"""

CATEGORY_NAMES = {
    "P": "Motor / Powertrain",
    "C": "Travagem / Chassis (inclui ABS)",
    "B": "Carroçaria",
    "U": "Rede / Comunicação",
}

CATEGORY_ICONS = {
    "P": "🔧",
    "C": "🛑",
    "B": "🚪",
    "U": "🔗",
}


def decode_dtc_bytes(byte1, byte2):
    """Converte 2 bytes (ex.: 0x03, 0x01) no código standard 'P0301'."""

    first_digit_map = {0: "P", 1: "C", 2: "B", 3: "U"}

    category_bits = (byte1 & 0xC0) >> 6
    second_digit = (byte1 & 0x30) >> 4
    third_digit = byte1 & 0x0F

    letter = first_digit_map[category_bits]

    code = f"{letter}{second_digit}{third_digit:X}{byte2:02X}"

    return code


def is_generic(code):
    """SAE genérico quando o 2º carácter é '0' ou '2'; '1' e '3' são
    tipicamente reservados ao fabricante."""

    return len(code) >= 2 and code[1] in ("0", "2")


def category_of(code):
    return CATEGORY_NAMES.get(code[0], "Desconhecida") if code else "Desconhecida"


# Base de descrições dos códigos genéricos (SAE) mais comuns.
# Foca-se nos que aparecem com mais frequência em oficina.
DESCRIPTIONS = {
    # --- P0100-P0199: Admissão / medição de ar e combustível ---
    "P0100": "Circuito do caudalímetro (MAF) — problema",
    "P0101": "Caudalímetro (MAF) — sinal fora de gama",
    "P0102": "Caudalímetro (MAF) — sinal baixo",
    "P0103": "Caudalímetro (MAF) — sinal alto",
    "P0110": "Sensor de temperatura do ar de admissão — circuito",
    "P0113": "Sensor de temperatura do ar de admissão — sinal alto",
    "P0116": "Sensor de temperatura do líquido de refrigeração — fora de gama",
    "P0117": "Sensor de temperatura do líquido de refrigeração — sinal baixo",
    "P0118": "Sensor de temperatura do líquido de refrigeração — sinal alto",
    "P0120": "Sensor de posição da borboleta — circuito",
    "P0125": "Temperatura insuficiente para malha fechada de combustível",
    "P0128": "Termostato — temperatura abaixo do valor regulado",
    "P0130": "Sonda lambda (Banco 1, Sensor 1) — circuito",
    "P0131": "Sonda lambda (Banco 1, Sensor 1) — tensão baixa",
    "P0132": "Sonda lambda (Banco 1, Sensor 1) — tensão alta",
    "P0133": "Sonda lambda (Banco 1, Sensor 1) — resposta lenta",
    "P0134": "Sonda lambda (Banco 1, Sensor 1) — sem atividade detetada",
    "P0135": "Sonda lambda (Banco 1, Sensor 1) — aquecedor com avaria",
    "P0136": "Sonda lambda (Banco 1, Sensor 2) — circuito",
    "P0141": "Sonda lambda (Banco 1, Sensor 2) — aquecedor com avaria",
    "P0170": "Fuel Trim (Banco 1) — fora dos limites",
    "P0171": "Mistura demasiado pobre (Banco 1)",
    "P0172": "Mistura demasiado rica (Banco 1)",
    "P0174": "Mistura demasiado pobre (Banco 2)",
    "P0175": "Mistura demasiado rica (Banco 2)",

    # --- P0200-P0299: Injetores / cilindros ---
    "P0200": "Circuito dos injetores — problema",
    "P0201": "Injetor do cilindro 1 — circuito",
    "P0202": "Injetor do cilindro 2 — circuito",
    "P0203": "Injetor do cilindro 3 — circuito",
    "P0204": "Injetor do cilindro 4 — circuito",
    "P0217": "Motor — sobreaquecimento",
    "P0230": "Circuito primário da bomba de combustível",

    # --- P0300-P0399: Falhas de ignição (misfire) ---
    "P0300": "Falha de ignição aleatória / múltipla detetada",
    "P0301": "Falha de ignição no cilindro 1",
    "P0302": "Falha de ignição no cilindro 2",
    "P0303": "Falha de ignição no cilindro 3",
    "P0304": "Falha de ignição no cilindro 4",
    "P0305": "Falha de ignição no cilindro 5",
    "P0306": "Falha de ignição no cilindro 6",
    "P0325": "Sensor de detonação (Knock) — circuito",
    "P0335": "Sensor de posição da cambota (CKP) — circuito",
    "P0339": "Sensor de posição da cambota — sinal intermitente",
    "P0340": "Sensor de posição da árvore de cames (CMP) — circuito",
    "P0350": "Bobina de ignição — circuito primário/secundário",

    # --- P0400-P0499: EGR / EVAP / emissões ---
    "P0401": "Fluxo insuficiente no sistema EGR",
    "P0402": "Fluxo excessivo no sistema EGR",
    "P0420": "Eficiência do catalisador abaixo do limite (Banco 1)",
    "P0430": "Eficiência do catalisador abaixo do limite (Banco 2)",
    "P0440": "Sistema EVAP — avaria genérica",
    "P0441": "Fluxo incorreto de purga no sistema EVAP",
    "P0442": "Sistema EVAP — fuga pequena detetada",
    "P0446": "Sistema EVAP — circuito de ventilação obstruído",
    "P0455": "Sistema EVAP — fuga grande detetada",
    "P0456": "Sistema EVAP — fuga muito pequena detetada",

    # --- P0500-P0599: Velocidade / ralenti / diversos ---
    "P0500": "Sensor de velocidade do veículo (VSS) — sem sinal",
    "P0505": "Sistema de controlo de ralenti — avaria",
    "P0506": "Ralenti abaixo do valor esperado",
    "P0507": "Ralenti acima do valor esperado",
    "P0562": "Tensão do sistema abaixo do normal",
    "P0563": "Tensão do sistema acima do normal",

    # --- P0600-P0699: Módulo de controlo ---
    "P0601": "Memória interna do módulo (ECM/PCM) — erro de checksum",
    "P0602": "Programação do módulo — não programado",
    "P0603": "Memória de reserva (KAM) — erro",
    "P0606": "Módulo de controlo do motor — desempenho do processador",

    # --- P0700-P0799: Transmissão ---
    "P0700": "Sistema de transmissão — avaria detetada (ver módulo TCM)",
    "P0715": "Sensor de velocidade de entrada da transmissão — circuito",
    "P0720": "Sensor de velocidade de saída da transmissão — circuito",
    "P0730": "Relação de caixa incorreta",
    "P0740": "Circuito do conversor de binário (embraiagem)",

    # --- C0xxx genéricos: chassis / travagem (inclui ABS) ---
    "C0035": "Sensor de velocidade da roda dianteira esquerda — circuito",
    "C0040": "Sensor de velocidade da roda dianteira direita — circuito",
    "C0045": "Sensor de velocidade da roda traseira esquerda — circuito",
    "C0050": "Sensor de velocidade da roda traseira direita — circuito",
    "C0110": "Motor da bomba do ABS — circuito",
    "C0121": "Válvula do circuito hidráulico do ABS — avaria",
    "C0161": "Interruptor das luzes de travagem — circuito",
    "C0196": "Sensor de guinada (Yaw) — circuito",
    "C0200": "Referência do sistema de travagem — avaria genérica",

    # --- B0xxx genéricos: carroçaria ---
    "B0001": "Airbag do condutor — circuito de disparo",
    "B0002": "Airbag do passageiro — circuito de disparo",
    "B0012": "Pré-tensor do cinto — circuito (lado condutor)",
    "B0100": "Módulo de airbags — avaria interna",
    "B1318": "Tensão da bateria — baixa (comum a vários fabricantes)",

    # --- U0xxx genéricos: rede / comunicação CAN ---
    "U0001": "Bus de dados CAN de alta velocidade — circuito",
    "U0100": "Perda de comunicação com o módulo do motor (ECM/PCM)",
    "U0101": "Perda de comunicação com a caixa de velocidades (TCM)",
    "U0121": "Perda de comunicação com o módulo do ABS",
    "U0140": "Perda de comunicação com o módulo da carroçaria (BCM)",
    "U0155": "Perda de comunicação com o quadro de instrumentos",
    "U0164": "Perda de comunicação com o módulo do ar condicionado",
    "U0401": "Dados inválidos recebidos do módulo do motor",
    "U0402": "Dados inválidos recebidos da caixa de velocidades",
}


def describe(code):

    if code in DESCRIPTIONS:
        return DESCRIPTIONS[code]

    if is_generic(code):
        return "Código genérico (SAE) sem descrição na base de dados local."

    return "Código específico do fabricante — sem base de dados pública fiável."


def build_dtc(code, status="Confirmado"):

    from core.dtc import DTC

    return DTC(
        code=code,
        description=describe(code),
        category=category_of(code),
        category_letter=code[0] if code else "?",
        generic=is_generic(code),
        status=status,
    )
