from time import perf_counter
from utils.logger import logger  # j'utilise ton logger existant

class SectionTimer:
    """Chronomètre de sections avec logs détaillés."""
    def __init__(self, title: str = "get_last_image"):
        self.title = title
        self.t0 = perf_counter()
        self.t_last = self.t0
        self.sections = []

    def mark(self, name: str):
        now = perf_counter()
        self.sections.append((name, (now - self.t_last) * 1000.0))  # ms
        self.t_last = now

    def end(self):
        total_ms = (perf_counter() - self.t0) * 1000.0
        # niveau debug pour le détail, et info pour le total
        for name, dt in self.sections:
            logger.info(f"[{self.title}] {name:<25} {dt:8.2f} ms")
        logger.info(f"[{self.title}] TOTAL{'':<21} {total_ms:8.2f} ms")

