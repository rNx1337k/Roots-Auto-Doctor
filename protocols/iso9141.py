class ISO9141:

    def __init__(self, interface):

        self.interface = interface

    def initialize(self):

        raise NotImplementedError

    def request(self, data):

        raise NotImplementedError