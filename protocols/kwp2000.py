class KWP2000:

    def __init__(self, interface):

        self.interface = interface

    def connect(self):

        raise NotImplementedError

    def identify(self):

        raise NotImplementedError

    def read_dtc(self):

        raise NotImplementedError