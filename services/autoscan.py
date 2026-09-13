class AutoScan:

    def __init__(self):

        self.results = []

    def clear(self):

        self.results.clear()

    def add(
        self,
        address,
        name,
        status
    ):

        self.results.append({
            "address": address,
            "name": name,
            "status": status
        })