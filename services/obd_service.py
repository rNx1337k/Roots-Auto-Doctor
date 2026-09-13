class OBDService:

    def __init__(
        self,
        obd
    ):

        self.obd = obd

    def identify_vehicle(self):

        return {
            "vin": self.obd.vin()
        }

    def read_faults(self):

        return self.obd.trouble_codes()

    def read_live_data(self):

        return {
            "rpm": self.obd.rpm(),
            "coolant": self.obd.coolant_temperature(),
            "speed": self.obd.speed(),
            "maf": self.obd.maf()
        }