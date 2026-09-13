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
        timeout=1
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
            timeout=self.timeout
        )

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

    def receive(self, size=4096):

        if not self.is_connected():
            raise RuntimeError(
                "Interface não conectada."
            )

        return self.serial.read(size)