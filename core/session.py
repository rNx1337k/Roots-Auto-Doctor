import json
from datetime import datetime


class DiagnosticSession:

    def __init__(self):

        self.started = datetime.now()
        self.vehicle = {}
        self.requests = []
        self.responses = []

    def record(
        self,
        request,
        response
    ):

        self.requests.append(request)
        self.responses.append(response)

    def save(self, filename):

        data = {
            "started": self.started.isoformat(),
            "vehicle": self.vehicle,
            "requests": self.requests,
            "responses": self.responses
        }

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )