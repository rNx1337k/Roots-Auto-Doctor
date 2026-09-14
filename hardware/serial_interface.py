import serial

from serial.tools import list_ports

from .interface import DiagnosticInterface


class SerialInterface(
    DiagnosticInterface
):

    def __init__(
        self,
        port,
        baudrate=38400,
        timeout=3.0
    ):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.serial = None

    @staticmethod
    def ports():

        result = []

        for port in list_ports.comports():

            result.append({
                "device": port.device,
                "description": port.description,
                "manufacturer": port.manufacturer
            })

        return result

    def connect(self):

        self.serial = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout,
            write_timeout=self.timeout
        )

        # Limpa lixo que possa ter ficado no buffer de uma sessão
        # anterior antes de começarmos a comunicar com o adaptador.
        try:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except Exception:
            pass

        return self.is_connected()

    def disconnect(self):

        if self.serial:
            self.serial.close()

        self.serial = None

    def is_connected(self):

        return (
            self.serial is not None
            and self.serial.is_open
        )

    def send(self, data):

        if not self.is_connected():
            raise RuntimeError(
                "Interface não conectada."
            )

        self.serial.write(data)
        self.serial.flush()

    def receive(self, size=4096):

        if not self.is_connected():
            raise RuntimeError(
                "Interface não conectada."
            )

        return self.serial.read(size)

    def receive_until(self, terminator=b">", size=4096):
        """Lê até encontrar o terminador (o prompt '>' do ELM327) em
        vez de um bloco de tamanho fixo — devolve assim que a resposta
        completa chega, sem esperar sempre pelo timeout todo. Sem isto,
        cada comando fica preso ~1s extra, o que é muito notório em
        dados ao vivo e faz a app parecer lenta/pastosa no carro."""

        if not self.is_connected():
            raise RuntimeError(
                "Interface não conectada."
            )

        return self.serial.read_until(terminator, size=size)