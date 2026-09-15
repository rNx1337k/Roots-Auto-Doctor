"""
Driver para adaptadores compatíveis com o chipset ELM327.
Trata da inicialização (comandos AT), do envio de comandos OBD-II
e da limpeza das respostas em bruto devolvidas pelo adaptador.
"""

import re
import threading
import time


class ELM327Error(Exception):
    """Erro de comunicação ou de protocolo com o adaptador ELM327."""


class ELM327:

    PROMPT = ">"

    INIT_SEQUENCE = [
        "ATE0",   # desliga eco dos comandos
        "ATL0",   # desliga line-feeds
        "ATS0",   # desliga espaços na resposta
        "ATH0",   # desliga cabeçalhos
        "ATAL",   # permite mensagens longas (VIN, multi-PID)
        "ATAT1",  # adaptive timing (NÃO é ATR1 — ATR1 liga respostas)
        "ATSP0",  # protocolo automático
    ]

    CAN_CODES = {"6", "7", "8", "9", "A", "B", "C"}

    def __init__(self, interface, logger=None):
        self.interface = interface
        self.logger = logger
        self.initialized = False
        self.protocol_name = None
        self.protocol_code = None
        self.is_can = False
        self._fast_mode = False
        self._log_enabled = True
        self._lock = threading.RLock()

    def initialize(self):
        from app.config import SERIAL_RESET_TIMEOUT, SERIAL_TIMEOUT

        with self._lock:
            if hasattr(self.interface, "flush"):
                self.interface.flush()

            if hasattr(self.interface, "set_timeout"):
                self.interface.set_timeout(SERIAL_RESET_TIMEOUT)

            # ATZ reinicia o chip. A resposta (versão + '>') chega sozinha;
            # não fazemos sleep extra depois de já ter o prompt.
            self._write("ATZ", delay=0.0, flush_first=True)

            if hasattr(self.interface, "set_timeout"):
                self.interface.set_timeout(SERIAL_TIMEOUT)

            for command in self.INIT_SEQUENCE:
                self._write(command, delay=0.02)

            self._apply_performance_settings()
            self.initialized = True

    def _apply_performance_settings(self):
        try:
            self._write("ATST0A", delay=0.02)
        except Exception:
            pass

    def set_fast_mode(self, enabled=True):
        with self._lock:
            self._fast_mode = bool(enabled)
            self._log_enabled = not self._fast_mode

            if hasattr(self.interface, "set_timeout"):
                from app.config import SERIAL_TIMEOUT, SERIAL_LIVE_TIMEOUT
                self.interface.set_timeout(
                    SERIAL_LIVE_TIMEOUT if self._fast_mode else SERIAL_TIMEOUT
                )

            try:
                self._write("ATST05" if self._fast_mode else "ATST0A", delay=0.0)
            except Exception:
                pass

    def detect_protocol(self):
        response = self._write("ATDPN")
        text = " ".join(self._clean_lines(response))
        self.protocol_code = self._extract_protocol_code(text)
        self.is_can = self.protocol_code in self.CAN_CODES
        self.protocol_name = self._describe_protocol(self.protocol_code)
        return self.protocol_name

    def battery_voltage(self):
        response = self._write("ATRV")
        text = " ".join(self._clean_lines(response))
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group())
        except ValueError:
            return None

    @staticmethod
    def _extract_protocol_code(raw):
        code = (raw or "").replace(" ", "").strip("\r\n>").upper()
        code = code.lstrip("A")
        if not code:
            return ""
        return code[0]

    def _describe_protocol(self, code):
        names = {
            "0": "Automático",
            "1": "SAE J1850 PWM",
            "2": "SAE J1850 VPW",
            "3": "ISO 9141-2",
            "4": "ISO 14230-4 (KWP2000, 5 baud)",
            "5": "ISO 14230-4 (KWP2000, fast init)",
            "6": "ISO 15765-4 (CAN, 11 bit, 500 kbps)",
            "7": "ISO 15765-4 (CAN, 29 bit, 500 kbps)",
            "8": "ISO 15765-4 (CAN, 11 bit, 250 kbps)",
            "9": "ISO 15765-4 (CAN, 29 bit, 250 kbps)",
            "A": "SAE J1939 (CAN, 29 bit, 250 kbps)",
            "B": "USER1 (CAN, 11 bit, 125 kbps)",
            "C": "USER2 (CAN, 11 bit, 50 kbps)",
        }
        return names.get(code, f"Desconhecido ({code})" if code else "—")

    def command(self, command, delay=None):
        """Envia um comando AT/OBD validado e devolve linhas limpas."""
        command = str(command or "").strip().upper()
        if not command or any(ch in command for ch in "\r\n"):
            raise ValueError("Comando OBD inválido.")
        if not re.fullmatch(r"[0-9A-Z? .]+", command):
            raise ValueError("Comando OBD contém caracteres inválidos.")

        if not self.initialized:
            self.initialize()

        if delay is None:
            delay = 0.0 if self._fast_mode else 0.01

        raw = self._write(command, delay=delay)
        return self._clean_lines(raw)

    def probe(self):
        """Resposta curta para saber se há um ELM327 na porta/baud actuais."""
        raw = self._write("ATI", delay=0.05, flush_first=True)
        text = raw.upper()
        return "ELM" in text or "OBD" in text or ">" in text

    def _write(self, command, delay=0.01, flush_first=False):
        with self._lock:
            if flush_first and hasattr(self.interface, "flush"):
                self.interface.flush()

            payload = f"{command}\r".encode("ascii", errors="ignore")
            self.interface.send(payload)

            if self.logger and self._log_enabled:
                self.logger.log(command, direction="TX")

            if delay and delay > 0:
                time.sleep(delay)

            text = self._read_response()

            if self.logger and self._log_enabled:
                for line in self._clean_lines(text):
                    self.logger.log(line, direction="RX")

            return text

    def _read_response(self):
        if hasattr(self.interface, "receive_until"):
            raw = self.interface.receive_until(self.PROMPT.encode("ascii"))
            return raw.decode("ascii", errors="ignore")

        text = ""
        attempts = 0
        while self.PROMPT not in text and attempts < 20:
            chunk = self.interface.receive(4096)
            text += chunk.decode("ascii", errors="ignore")
            if self.PROMPT not in text:
                time.sleep(0.02)
            attempts += 1
        return text

    @staticmethod
    def _clean_lines(raw):
        lines = raw.replace("\r", "\n").split("\n")
        cleaned = []

        for line in lines:
            line = line.strip().strip(">").strip()
            if not line:
                continue
            if line.upper() in ("OK", "SEARCHING...", "SEARCHING", "STOPPED"):
                continue
            cleaned.append(line)

        return cleaned
