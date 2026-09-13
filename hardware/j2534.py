class J2534Interface:

    def __init__(self, dll_path=None):

        self.dll_path = dll_path
        self.connected = False

    def detect(self):

        return False

    def connect(self):

        raise NotImplementedError(
            "J2534 ainda não configurado."
        )

    def disconnect(self):

        self.connected = False

    def send(self, data):

        raise NotImplementedError

    def receive(self):

        raise NotImplementedError