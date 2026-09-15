APP_NAME = "Roots Auto Doctor"
APP_VERSION = "0.4.1"

# Baud padrão seguro para a maioria dos clones ELM327 baratos.
DEFAULT_OBD_BAUDRATE = 38400

# Ordem de tentativa quando a ligação está em "Auto".
BAUD_CANDIDATES = [38400, 115200, 9600, 57600]

# Timeout de leitura serial (segundos). Valor alto só para a fase de
# inicialização / identificação. Em streaming ao vivo o driver ELM327
# usa um timeout mais curto (ver SERIAL_LIVE_TIMEOUT).
SERIAL_TIMEOUT = 1.5
SERIAL_LIVE_TIMEOUT = 0.75
SERIAL_RESET_TIMEOUT = 3.0

# Intervalo alvo entre ciclos completos de leitura de PIDs (segundos).
LIVE_DATA_INTERVAL = 0.25

LIVE_DATA_PRESETS = {
    "Lento": 1.0,
    "Normal": 0.4,
    "Rápido": 0.2,
    "Máximo": 0.05,
}
LIVE_DATA_DEFAULT_PRESET = "Rápido"

# PIDs pré-seleccionados ao ligar (se a ECU os suportar).
DEFAULT_LIVE_PIDS = [0x0C, 0x0D, 0x05, 0x11]

# Quantos PIDs pedir de uma vez em CAN (ISO 15765). Clones fracos
# por vezes só devolvem o primeiro — há fallback automático.
CAN_PID_BATCH_SIZE = 6  # compatibilidade
CAN_MULTI_PID_REQUESTS = False  # pedidos multi-PID não são uniformes em ELM327/ECUs

LOGGER_MAX_LINES = 3000

SETTINGS_ORGANISATION = "RootsAutoDoctor"
SETTINGS_APPLICATION = "Roots Auto Doctor"
