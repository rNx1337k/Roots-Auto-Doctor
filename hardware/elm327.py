"""
Driver para adaptadores compatíveis com o chipset ELM327.
Trata da inicialização (comandos AT), do envio de comandos OBD-II
e da limpeza das respostas em bruto devolvidas pelo adaptador.
"""

import re
import time
import threading


class ELM327Error(Exception):
    """Erro de comunicação ou de protocolo com o adaptador ELM327."""


class ELM327:

    PROMPT = ">"

    INIT_SEQUENCE = [
        "ATZ",    # reset
        "ATE0",   # desliga eco dos comandos
        "ATL0",   # desliga line-feeds
        "ATS0",   # desliga espaços na resposta
        "ATH0",   # desliga cabeçalhos (respostas mais simples de ler)
        "ATSP0",  # protocolo automático
    ]

    def __init__(self, interface, logger=None):

        self.interface = interface
        self.logger = logger
        self.initialized = False
        self.protocol_name = None

        # O ELM327 é um canal half-duplex: só deve existir um pedido
        # pendente de cada vez. Isto é especialmente importante quando
        # Live Data e Gráficos estão ativos em simultâneo.
        self._io_lock = threading.RLock()

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def initialize(self):

        responses = []

        for command in self.INIT_SEQUENCE:
            # o ATZ obriga o chip a reiniciar-se fisicamente — dá-lhe
            # tempo a acordar antes do próximo comando, ou o adaptador
            # pode perder os primeiros carateres que lhe enviamos.
            delay = 1.2 if command == "ATZ" else 0.05
            responses.append(self._write(command, delay=delay))

        # Não exigimos uma mensagem específica: clones ELM327 variam
        # bastante no texto apresentado durante o arranque. Basta que o
        # adaptador tenha respondido a pelo menos um comando.
        if not any(response and response.strip() for response in responses):
            raise ELM327Error(
                "O adaptador não respondeu aos comandos de inicialização."
            )

        self.initialized = True

    def detect_protocol(self):
        """Pergunta ao adaptador que protocolo ficou ativo depois do
        primeiro pedido bem-sucedido (ATDPN)."""

        response = self._write("ATDPN")
        self.protocol_name = self._describe_protocol(response)
        return self.protocol_name

    def battery_voltage(self):
        """Lê a tensão OBD/bateria através do adaptador (comando
        'AT RV'). É o primeiro teste de sanidade a fazer num carro
        real: sem ~12V aqui, o problema é a ficha/fusível, não a app."""

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
    def _describe_protocol(code):

        code = (code or "").replace(" ", "").strip("\r\n>").lstrip("A")

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
        }

        return names.get(code, f"Desconhecido ({code})" if code else "—")

    # ------------------------------------------------------------------
    # Comunicação
    # ------------------------------------------------------------------

    def command(self, command, delay=0.02):
        """Envia um comando OBD-II (ex: '010C') e devolve a resposta
        já limpa, como lista de linhas em texto (sem o prompt '>')."""

        if not self.initialized:
            self.initialize()

        raw = self._write(command, delay=delay)

        return self._clean_lines(raw)

    def _write(self, command, delay=0.02):

        # Não permitir que dois threads misturem comandos/respostas no
        # mesmo adaptador. Sem este lock, duas páginas a ler em paralelo
        # podem receber a resposta destinada à outra.
        with self._io_lock:
            payload = f"{command}\r".encode("ascii", errors="ignore")

            self.interface.send(payload)

            if self.logger:
                self.logger.log(command, direction="TX")

            if delay:
                time.sleep(delay)

            text = self._read_response()

            if self.logger:
                for line in self._clean_lines(text):
                    self.logger.log(line, direction="RX")

            return text

    def _read_response(self):
        """Lê a resposta do adaptador até ao prompt '>'. Usa leitura
        bloqueante-até-terminador quando a interface a suporta — devolve
        assim que a resposta chega, em vez de esperar sempre pelo
        timeout completo, o que é essencial para dados ao vivo fluidos."""

        if hasattr(self.interface, "receive_until"):
            raw = self.interface.receive_until(self.PROMPT.encode("ascii"))
            return raw.decode("ascii", errors="ignore")

        # Reserva para interfaces sem leitura-até-terminador: vai
        # buscando blocos pequenos até encontrar o prompt ou esgotar
        # as tentativas.
        text = ""
        attempts = 0

        while self.PROMPT not in text and attempts < 20:

            chunk = self.interface.receive(4096)
            text += chunk.decode("ascii", errors="ignore")

            if self.PROMPT not in text:
                time.sleep(0.05)

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

            upper = line.upper()

            if upper in ("OK", "SEARCHING...", "SEARCHING"):
                continue

            if upper in (
                "NO DATA",
                "NODATA",
                "UNABLE TO CONNECT",
                "UNABLETOCONNECT",
                "BUS INIT: ERROR",
                "CAN ERROR",
                "BUFFER FULL",
                "STOPPED",
            ):
                cleaned.append(upper)
                continue

            cleaned.append(line)

        return cleaned
