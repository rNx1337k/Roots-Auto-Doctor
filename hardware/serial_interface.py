import serial

from serial.tools import list_ports

from .interface import DiagnosticInterface


class SerialInterface(DiagnosticInterface):

    def __init__(
        self,
        port,
        baudrate=38400,
        timeout=1.5,
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
                "manufacturer": port.manufacturer,
            })
        return result

    def connect(self):
        kwargs = {
            "port": self.port,
            "baudrate": self.baudrate,
            "timeout": self.timeout,
            "write_timeout": min(self.timeout, 1.0),
        }
        try:
            self.serial = serial.Serial(inter_byte_timeout=0.05, **kwargs)
        except TypeError:
            self.serial = serial.Serial(**kwargs)

        self.flush()
        return self.is_connected()

    def disconnect(self):
        if self.serial:
            try:
                self.serial.close()
            except Exception:
                pass
        self.serial = None

    def is_connected(self):
        return self.serial is not None and self.serial.is_open

    def set_timeout(self, timeout):
        self.timeout = timeout
        if self.serial and self.serial.is_open:
            self.serial.timeout = timeout
            self.serial.write_timeout = min(timeout, 1.0)

    def set_baudrate(self, baudrate):
        self.baudrate = baudrate
        if self.serial and self.serial.is_open:
            self.serial.baudrate = baudrate
            self.flush()

    def flush(self):
        if not self.is_connected():
            return
        try:
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
        except Exception:
            pass

    def send(self, data):
        if not self.is_connected():
            raise RuntimeError("Interface não conectada.")
        self.serial.write(data)
        self.serial.flush()

    def receive(self, size=4096):
        if not self.is_connected():
            raise RuntimeError("Interface não conectada.")
        return self.serial.read(size)

    def receive_until(self, terminator=b">", size=4096):
        if not self.is_connected():
            raise RuntimeError("Interface não conectada.")
        return self.serial.read_until(terminator, size=size)
