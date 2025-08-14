
from services.configurator import CONFIG
from utils.logger import logger

if CONFIG["global"].get("mode_simulator", False):
    logger.info("[TELESCOPE] - Running in simulator mode")
    from services.interfaces.simulator import SimulatorTelescope

    telescope_interface = SimulatorTelescope()
else:
    from services.interfaces.alpaca import AlpacaTelescope

    telescope_interface = AlpacaTelescope()
if not CONFIG["global"].get("mode_debug", False):
    telescope_interface.connect()







