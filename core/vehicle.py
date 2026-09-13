class Vehicle:

    def __init__(self):
        self.reset()

    def reset(self):

        self.connected = False

        self.vin = None
        self.make = None
        self.model = None
        self.year = None
        self.engine = None

        self.protocol = None

        self.ecus = []

    @property
    def identified(self):

        return any([
            self.vin,
            self.make,
            self.model,
            self.engine
        ])

    def update(self, **data):

        for key, value in data.items():

            if hasattr(self, key):
                setattr(
                    self,
                    key,
                    value
                )