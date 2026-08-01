# Logging module for LIFE_GPT
# Writes per-tick population statistics to CSV for later analysis

import csv
import os
from config import LOG_FILE
from file_utils import lock_file, unlock_file


_log_fh = None


def init_logging():
    """Open log file and write CSV header."""
    global _log_fh

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    write_header = not os.path.exists(LOG_FILE)
    lock_file(LOG_FILE)
    try:
        _log_fh = open(LOG_FILE, "a", newline="", encoding="utf-8")
        if write_header:
            writer = csv.writer(_log_fh)
            writer.writerow([
                "tick", "total_cells",
                "n_phot", "n_zoo", "n_poly",
                "avg_energy", "avg_mass", "avg_level",
                "max_energy", "born_this_tick",
            ])
            _log_fh.flush()
    finally:
        unlock_file(LOG_FILE)


def log_tick(tick: int, cells: list, born: int = 0):
    """Record one tick of population data."""
    global _log_fh
    if _log_fh is None:
        return

    n = len(cells)
    if n == 0:
        row = [tick, 0, 0, 0, 0, 0.0, 0.0, 0, 0.0, born]
    else:
        n_phot = sum(1 for c in cells if c.genome.diet == 0)
        n_zoo = sum(1 for c in cells if c.genome.diet == 1)
        n_poly = sum(1 for c in cells if c.genome.diet == 2)

        avg_e = sum(c.energy for c in cells) / n
        avg_m = sum(c.genome.mass for c in cells) / n
        avg_l = sum(c.level for c in cells) / n
        max_e = max((c.energy for c in cells), default=0.0)

        row = [tick, n, n_phot, n_zoo, n_poly,
               round(avg_e, 2), round(avg_m, 2), round(avg_l, 1),
               round(max_e, 1), born]

    lock_file(LOG_FILE)
    try:
        writer = csv.writer(_log_fh)
        writer.writerow(row)
        _log_fh.flush()
    finally:
        unlock_file(LOG_FILE)


def close_logging():
    """Flush and close log file."""
    global _log_fh
    if _log_fh is not None:
        _log_fh.flush()
        _log_fh.close()
        _log_fh = None