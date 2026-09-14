"""
Protocolo OBD-II genérico (SAE J1979 / ISO 15031), implementado sobre
um adaptador ELM327. Cobre os modos mais usados em diagnóstico:

    Modo 01 -> dados em tempo real (Live Data)
    Modo 02 -> freeze frame (fotografia dos sensores no momento da falha)
    Modo 03 -> códigos de falha confirmados
    Modo 04 -> apagar códigos de falha
    Modo 07 -> códigos de falha pendentes
    Modo 09 -> informação do veículo (VIN, nome da ECU)
"""

from services.pid_database import get_pid
from services.dtc_database import decode_dtc_bytes


class OBD2Error(Exception):
    pass


class OBD2:

    def __init__(self, adapter):
        self.adapter = adapter

    # ------------------------------------------------------------------
    # Infraestrutura de pedidos
    # ------------------------------------------------------------------

    def request(self, service, pid=None):

        command = f"{service:02X}"

        if pid is not None:
            command += f"{pid:02X}"

        lines = self.adapter.command(command)

        return self._to_bytes(lines, service, pid=pid)

    @staticmethod
    def _to_bytes(lines, service, pid=None):
        """Converte respostas ELM em payload puro.

        Ex.: ``41 0C 1A F8`` -> ``[0x1A, 0xF8]`` quando o pedido foi
        ``01 0C``. Também aceita linhas CAN com cabeçalho, como
        ``7E8 41 0C 1A F8``.
        """

        expected_prefix = f"{(service + 0x40):02X}"

        results = []

        for line in lines:

            raw_line = line.strip().upper()
            compact = raw_line.replace(" ", "")

            if not compact or compact in (
                "NODATA",
                "NO DATA",
                "?",
                "UNABLETOCONNECT",
                "UNABLE TO CONNECT",
                "BUS INIT: ERROR",
                "CAN ERROR",
                "STOPPED",
            ):
                continue

            # Alguns adaptadores mantêm os headers CAN ativos apesar de
            # AT H0. Aceita também respostas do tipo "7E8 41 0C ...".
            candidates = [compact]

            if " " in raw_line:
                parts = raw_line.split()
                for index, part in enumerate(parts):
                    if part == expected_prefix:
                        candidates.append("".join(parts[index:]))

            for candidate in candidates:
                if not all(c in "0123456789ABCDEF" for c in candidate):
                    continue

                if not candidate.startswith(expected_prefix):
                    continue

                data_hex = candidate[len(expected_prefix):]

                try:
                    data = bytes.fromhex(data_hex)
                except ValueError:
                    continue

                # Respostas de Modo 01/02/09 repetem o PID/InfoType
                # solicitado logo após o serviço de resposta.
                if pid is not None:
                    if not data or data[0] != pid:
                        continue
                    data = data[1:]

                if not data:
                    continue

                results.append(data)
                break

        return results

    # ------------------------------------------------------------------
    # Identificação
    # ------------------------------------------------------------------

    def supported_pids(self):
        """Devolve o conjunto de PIDs (Modo 01) que a ECU efetivamente
        suporta, consultando os bitmasks 00, 20, 40, 60..."""

        supported = set()
        base = 0x00

        while True:

            frames = self.request(0x01, base)

            if not frames:
                break

            bitmask = int.from_bytes(frames[0][-4:], "big")

            for offset in range(32):

                pid = base + offset + 1
                bit = 31 - offset

                if bitmask & (1 << bit):
                    supported.add(pid)

            # bit 0 indica se o próximo bloco (base+0x20) também existe
            if not (bitmask & 1):
                break

            base += 0x20

            if base > 0xC0:
                break

        return supported

    def vin(self):
        """Modo 09, InfoType 02 -> VIN (17 carateres ASCII)."""

        frames = self.request(0x09, 0x02)

        raw = b"".join(frames)

        # o primeiro byte de cada frame reagrupado costuma ser um
        # contador de mensagem (0x01, 0x02...) — filtra não-imprimíveis
        text = "".join(chr(b) for b in raw if 32 <= b <= 126)

        return text[-17:] if len(text) >= 17 else (text or None)

    def ecu_name(self):
        """Modo 09, InfoType 0A -> nome da ECU, quando suportado."""

        frames = self.request(0x09, 0x0A)

        raw = b"".join(frames)
        text = "".join(chr(b) for b in raw if 32 <= b <= 126).strip()

        return text or None

    # ------------------------------------------------------------------
    # Dados em tempo real (Live Data)
    # ------------------------------------------------------------------

    def read_pid(self, pid):
        """Lê e descodifica um único PID do Modo 01 usando a
        services.pid_database. Devolve (valor, unidade) ou (None, None)."""

        definition = get_pid(pid)

        if not definition:
            return None, None

        frames = self.request(0x01, pid)

        if not frames:
            return None, None

        data = frames[0]

        if len(data) < definition["bytes"]:
            return None, None

        try:
            value = definition["decode"](data)
        except Exception:
            return None, None

        return value, definition["unit"]

    # ------------------------------------------------------------------
    # Códigos de falha
    # ------------------------------------------------------------------

    def trouble_codes(self, pending=False, permanent=False):
        """Lê os DTCs do Modo 03 (confirmados), 07 (pendentes) ou
        0A (permanentes — não podem ser apagados pelo Modo 04) e
        devolve uma lista de códigos standard (ex.: ['P0301', 'C0035'])."""

        if permanent:
            service = 0x0A
        elif pending:
            service = 0x07
        else:
            service = 0x03

        frames = self.request(service)

        codes = []

        for data in frames:

            # cada DTC ocupa 2 bytes; 00 00 significa "sem código"
            for i in range(0, len(data) - 1, 2):

                b1, b2 = data[i], data[i + 1]

                if b1 == 0 and b2 == 0:
                    continue

                codes.append(decode_dtc_bytes(b1, b2))

        return codes

    def clear_trouble_codes(self):
        self.request(0x04)
        return True

    def freeze_frame(self, pid, frame_number=0):
        """Modo 02 — mesma estrutura do Modo 01, mas para a fotografia
        de sensores guardada no momento em que a falha ocorreu."""

        definition = get_pid(pid)

        if not definition:
            return None, None

        command = f"02{pid:02X}{frame_number:02X}"
        lines = self.adapter.command(command)
        frames = self._to_bytes(lines, 0x02, pid=pid)

        if not frames:
            return None, None

        data = frames[0]

        if len(data) < definition["bytes"]:
            return None, None

        try:
            value = definition["decode"](data)
        except Exception:
            return None, None

        return value, definition["unit"]

    # ------------------------------------------------------------------
    # Prontidão para inspeção / emissões (Readiness Monitors)
    # ------------------------------------------------------------------

    # Monitores contínuos (existem em qualquer veículo OBD-II)
    CONTINUOUS_MONITORS = [
        ("Falhas de ignição (Misfire)", 2),
        ("Sistema de combustível", 1),
        ("Componentes (Comprehensive)", 0),
    ]

    # Monitores não-contínuos — motor a gasolina / ignição por faísca
    SPARK_MONITORS = [
        ("Catalisador", 0),
        ("Catalisador aquecido", 1),
        ("Sistema EVAP", 2),
        ("Ar secundário", 3),
        ("Sensor A/C (reservado)", 4),
        ("Sonda lambda", 5),
        ("Aquecedor da sonda lambda", 6),
        ("Sistema EGR", 7),
    ]

    # Monitores não-contínuos — motor a gasóleo / ignição por compressão
    COMPRESSION_MONITORS = [
        ("Catalisador NMHC", 0),
        ("Sistema NOx / SCR", 1),
        ("Pressão de sobrealimentação (turbo)", 3),
        ("Sensor de gases de escape", 5),
        ("Filtro de partículas (FAP/DPF)", 6),
        ("Sistema EGR / VVT", 7),
    ]

    def readiness(self):
        """Devolve o estado dos monitores de prontidão para inspeção
        (Modo 01, PID 01) — 'pronto' / 'não pronto' por sistema, tal
        como usado nas inspeções periódicas obrigatórias (emissões)."""

        frames = self.request(0x01, 0x01)

        if not frames or len(frames[0]) < 4:
            return None

        a, b, c, d = frames[0][:4]

        mil_on = bool(a & 0x80)
        dtc_count = a & 0x7F

        compression = bool(b & 0x08)

        monitors = []

        for name, bit in self.CONTINUOUS_MONITORS:
            monitors.append({
                "name": name,
                "supported": True,
                "ready": not bool(b & (1 << bit)),
            })

        table = self.COMPRESSION_MONITORS if compression else self.SPARK_MONITORS

        for name, bit in table:

            supported = bool(c & (1 << bit))

            if not supported:
                continue

            monitors.append({
                "name": name,
                "supported": True,
                "ready": not bool(d & (1 << bit)),
            })

        return {
            "mil_on": mil_on,
            "dtc_count": dtc_count,
            "ignition_type": "Compressão (gasóleo)" if compression else "Faísca (gasolina)",
            "monitors": monitors,
        }
