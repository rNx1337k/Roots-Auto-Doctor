class ConnectionManager:

    def __init__(self):

        self.interface = None
        self.protocol = None

    def set_interface(self, interface):

        self.interface = interface

    def connect(self):

        if not self.interface:
            raise RuntimeError(
                "Nenhuma interface selecionada."
            )

        return self.interface.connect()

    def disconnect(self):

        if self.interface:
            self.interface.disconnect()

    def connected(self):

        return (
            self.interface is not None
            and self.interface.is_connected()
        )