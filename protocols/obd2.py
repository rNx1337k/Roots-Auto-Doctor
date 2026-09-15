"""
Protocolo OBD-II genérico (SAE J1979 / ISO 15031), implementado sobre
um adaptador ELM327.
"""

from app.config import CAN_PID_BATCH_SIZE
from services.pid_database import get_pid
from services.dtc_database import decode_dtc_bytes


class OBD2Error(Exception):
    pass


class OBD2:

    def __init__(self, adapter):
        self.adapter = adapter
        self._batch_ok = None

    def request(self, service, pid=None):
        command = f"{service:02X}"
        if pid is not None:
            command += f"{pid:02X}"
        lines = self.adapter.command(command)
        return self._to_bytes(lines, service, pid=pid)

    @staticmethod
    def _to_bytes(lines, service, pid=None):
        expected_prefix = f"{(service + 0x40):02X}"
        results = []

        for line in lines:
            line = line.replace(" ", "").upper()

            if not line or line in ("NODATA", "?", "UNABLETOCONNECT", "BUSY", "ERROR"):
                continue

            if not all(c in "0123456789ABCDEF" for c in line):
                continue

            if not line.startswith(expected_prefix):
                continue

            payload = line[len(expected_prefix):]

            if pid is not None and len(payload) >= 2:
                echoed = payload[:2]
                if echoed == f"{pid:02X}":
                    payload = payload[2:]

            if not payload:
                continue

            try:
                results.append(bytes.fromhex(payload))
            except ValueError:
                continue

        return results

    def supported_pids(self):
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

            if not (bitmask & 1):
                break

            base += 0x20
            if base > 0xC0:
                break

        return supported

    def vin(self):
        frames = self.request(0x09, 0x02)
        raw = b"".join(frames)
        text = "".join(chr(b) for b in raw if 32 <= b <= 126)
        return text[-17:] if len(text) >= 17 else (text or None)

    def ecu_name(self):
        frames = self.request(0x09, 0x0A)
        raw = b"".join(frames)
        text = "".join(chr(b) for b in raw if 32 <= b <= 126).strip()
        return text or None

    def read_pid(self, pid):
        definition = get_pid(pid)
        if not definition:
            return None, None

        frames = self.request(0x01, pid)
        if not frames:
            return None, None

        return self._decode_pid(pid, frames[0])

    def read_pids(self, pids):
        """Lê vários PIDs. Em CAN tenta um pedido em lote (muito mais
        rápido); se o clone não cooperar, cai automaticamente para
        pedidos individuais."""
        pids = list(pids)
        result = {}
        if not pids:
            return result

        is_can = bool(getattr(self.adapter, "is_can", False))
        use_batch = is_can and self._batch_ok is not False and len(pids) > 1

        if not use_batch:
            for pid in pids:
                result[pid] = self.read_pid(pid)
            return result

        size = max(2, int(CAN_PID_BATCH_SIZE))
        for i in range(0, len(pids), size):
            batch = pids[i:i + size]
            parsed = self._read_pid_batch(batch)
            if parsed:
                self._batch_ok = True
                for pid in batch:
                    data = parsed.get(pid)
                    result[pid] = self._decode_pid(pid, data) if data else (None, None)
            else:
                self._batch_ok = False
                for pid in batch:
                    result[pid] = self.read_pid(pid)
        return result

    def _read_pid_batch(self, pids):
        command = "01" + "".join(f"{pid:02X}" for pid in pids)
        lines = self.adapter.command(command)
        return self._parse_mode01_lines(lines)

    @staticmethod
    def _parse_mode01_lines(lines):
        """Extrai {pid: data_bytes} de uma ou mais linhas 41XX..."""
        found = {}
        blob = ""
        for line in lines:
            line = line.replace(" ", "").upper()
            if not line or line in ("NODATA", "?", "UNABLETOCONNECT", "BUSY", "ERROR"):
                continue
            if all(c in "0123456789ABCDEF" for c in line):
                blob += line

        i = 0
        while i + 4 <= len(blob):
            if blob[i:i + 2] != "41":
                i += 2
                continue
            try:
                pid = int(blob[i + 2:i + 4], 16)
            except ValueError:
                i += 2
                continue

            definition = get_pid(pid)
            nbytes = definition["bytes"] if definition else 2
            start = i + 4
            end = start + nbytes * 2
            if end > len(blob):
                break
            try:
                found[pid] = bytes.fromhex(blob[start:end])
            except ValueError:
                i += 2
                continue
            i = end
        return found

    @staticmethod
    def _decode_pid(pid, data):
        definition = get_pid(pid)
        if not definition or data is None:
            return None, None
        if len(data) < definition["bytes"]:
            return None, None
        try:
            value = definition["decode"](data)
        except Exception:
            return None, None
        return value, definition["unit"]

    def trouble_codes(self, pending=False, permanent=False):
        if permanent:
            service = 0x0A
        elif pending:
            service = 0x07
        else:
            service = 0x03

        frames = self.request(service)
        codes = []

        for data in frames:
            payload = self._dtc_payload(data)
            for i in range(0, len(payload) - 1, 2):
                b1, b2 = payload[i], payload[i + 1]
                if b1 == 0 and b2 == 0:
                    continue
                codes.append(decode_dtc_bytes(b1, b2))

        return codes

    @staticmethod
    def _dtc_payload(data):
        """Em CAN o primeiro byte após 43/47/4A é o nº de DTCs.
        Em ISO/KWP os DTCs começam logo. Heurística: se o 1º byte
        parece um contador (0–16) e o resto tem exactamente 2*N bytes,
        saltamo-lo."""
        if not data:
            return data
        count = data[0]
        if 0 <= count <= 16 and len(data) == 1 + 2 * count:
            return data[1:]
        return data

    def clear_trouble_codes(self):
        self.request(0x04)
        return True

    def freeze_frame(self, pid, frame_number=0):
        definition = get_pid(pid)
        if not definition:
            return None, None

        command = f"02{pid:02X}{frame_number:02X}"
        lines = self.adapter.command(command)
        frames = self._to_bytes(lines, 0x02, pid=pid)

        if not frames:
            return None, None

        data = frames[0]
        if len(data) >= definition["bytes"] + 1:
            # alguns adaptadores ecoam também o nº de frame
            if data[0] == frame_number:
                data = data[1:]

        return self._decode_pid(pid, data)

    CONTINUOUS_MONITORS = [
        ("Falhas de ignição (Misfire)", 2),
        ("Sistema de combustível", 1),
        ("Componentes (Comprehensive)", 0),
    ]

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

    COMPRESSION_MONITORS = [
        ("Catalisador NMHC", 0),
        ("Sistema NOx / SCR", 1),
        ("Pressão de sobrealimentação (turbo)", 3),
        ("Sensor de gases de escape", 5),
        ("Filtro de partículas (FAP/DPF)", 6),
        ("Sistema EGR / VVT", 7),
    ]

    def readiness(self):
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
