from datetime import datetime

from app.config import LOGGER_MAX_LINES


class Logger:

    def __init__(self, on_message=None):
        self.messages = []
        self.on_message = on_message

    def log(self, message, direction=None):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if direction:
            line = f"{timestamp}  {direction:<3}  {message}"
        else:
            line = f"{timestamp}  {message}"

        self.messages.append(line)

        if len(self.messages) > LOGGER_MAX_LINES:
            self.messages = self.messages[-(LOGGER_MAX_LINES // 2):]

        if self.on_message:
            self.on_message(line)

        return line

    def clear(self):
        self.messages.clear()
