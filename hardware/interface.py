from abc import ABC, abstractmethod


class DiagnosticInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self):
        pass

    @abstractmethod
    def send(self, data):
        pass

    @abstractmethod
    def receive(self):
        pass