import time
import threading


class DataAcquisition:

    def __init__(
        self,
        callback,
        interval=1.0
    ):

        self.callback = callback
        self.interval = interval

        self.running = False
        self.thread = None

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        self.running = False

    def _run(self):

        while self.running:

            try:

                data = self.callback()

                # Aqui enviaremos os dados
                # para a interface.

                print(data)

            except Exception as error:

                print(
                    f"Acquisition error: {error}"
                )

            time.sleep(
                self.interval
            )