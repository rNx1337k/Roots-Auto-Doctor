"""Aquisição periódica de dados fora da thread da interface."""

import threading
from typing import Callable, Optional


class DataAcquisition:
    """Executa uma função de aquisição periodicamente numa thread daemon."""

    def __init__(
        self,
        callback: Callable[[], object],
        interval: float = 1.0,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        if not callable(callback):
            raise TypeError("callback tem de ser chamável.")

        if interval <= 0:
            raise ValueError("interval tem de ser superior a zero.")

        self.callback = callback
        self.interval = float(interval)
        self.on_error = on_error

        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        """Inicia a aquisição se ainda não estiver em execução."""
        with self._lock:
            if self.running:
                return

            self._stop_event.clear()
            self.running = True
            self.thread = threading.Thread(
                target=self._run,
                name="RootsAutoDoctor-DataAcquisition",
                daemon=True,
            )
            self.thread.start()

    def stop(self, wait: bool = False, timeout: float = 2.0):
        """Solicita paragem. Opcionalmente aguarda o fim da thread."""
        with self._lock:
            self.running = False
            thread = self.thread
            self._stop_event.set()

        if wait and thread and thread.is_alive():
            thread.join(timeout=max(0.0, timeout))

    def _run(self):
        try:
            while not self._stop_event.is_set():
                try:
                    self.callback()
                except Exception as error:
                    if self.on_error:
                        try:
                            self.on_error(error)
                        except Exception:
                            pass

                # Event.wait permite parar imediatamente, sem esperar
                # pelo intervalo completo.
                if self._stop_event.wait(self.interval):
                    break
        finally:
            with self._lock:
                self.running = False
                if self.thread is threading.current_thread():
                    self.thread = None
