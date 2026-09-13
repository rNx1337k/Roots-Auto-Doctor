"""
Driver para adaptadores compatíveis com o chipset ELM327.
Trata da inicialização (comandos AT), do envio de comandos OBD-II
e da limpeza das respostas em bruto devolvidas pelo adaptador.
"""

import time


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

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def initialize(self):

        for command in self.INIT_SEQUENCE:
            self._write(command)

        self.initialized = True

    def detect_protocol(self):
        """Pergunta ao adaptador que protocolo ficou ativo depois do
        primeiro pedido bem-sucedido (ATDPN)."""

        response = self._write("ATDPN")
        self.protocol_name = self._describe_protocol(response)
        return self.protocol_name

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

    def command(self, command, delay=0.15):
        """Envia um comando OBD-II (ex: '010C') e devolve a resposta
        já limpa, como lista de linhas em texto (sem o prompt '>')."""

        if not self.initialized:
            self.initialize()

        raw = self._write(command, delay=delay)

        return self._clean_lines(raw)

    def _write(self, command, delay=0.3):

        payload = f"{command}\r".encode("ascii", errors="ignore")

        self.interface.send(payload)

        if self.logger:
            self.logger.log(command, direction="TX")

        time.sleep(delay)

        chunk = self.interface.receive(4096)
        text = chunk.decode("ascii", errors="ignore")

        # Alguns adaptadores respondem em vários blocos; espera um
        # pouco mais se ainda não recebeu o prompt de fim ('>').
        attempts = 0
        while self.PROMPT not in text and attempts < 8:
            time.sleep(0.1)
            more = self.interface.receive(4096)
            text += more.decode("ascii", errors="ignore")
            attempts += 1

        if self.logger:
            for line in self._clean_lines(text):
                self.logger.log(line, direction="RX")

        return text

    @staticmethod
    def _clean_lines(raw):

        lines = raw.replace("\r", "\n").split("\n")

        cleaned = []

        for line in lines:

            line = line.strip().strip(">").strip()

            if not line:
                continue

            if line.upper() in ("OK", "SEARCHING...", "SEARCHING"):
                continue

            cleaned.append(line)

        return cleaned
