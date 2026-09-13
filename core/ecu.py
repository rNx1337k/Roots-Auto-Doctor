class ECU:

    def __init__(
        self,
        address=None
    ):

        self.address = address

        self.name = None
        self.part_number = None
        self.software = None
        self.hardware = None

        self.protocol = None

        self.connected = False

        self.dtc = []
        self.data = {}