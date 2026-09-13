from .j2534 import J2534Interface


class DS150E(J2534Interface):

    NAME = "Delphi DS150E"

    def detect(self):

        return False