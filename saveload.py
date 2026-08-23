# ═══════════════════════════════════════════════════════════════════════
#  saveload.py — save / load helpers for LIFE_GPT
# ═══════════════════════════════════════════════════════════════════════
import os
import json

_project_dir = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(_project_dir, "saved_cells.json")


def locked_json_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        import fcntl

        with open(tmp, "r") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
        os.replace(tmp, path)
    except ImportError:
        # Windows doesn't have fcntl, skip file locking
        os.replace(tmp, path)


def save_cells(cells_to_save):
    data = []
    for c in cells_to_save[:50]:
        data.append(
            {
                "x": c.x,
                "y": c.y,
                "energy": c.energy,
                "level": c.level,
                "age": c.age,
                "exp": getattr(c, 'exp', 0.0),
                "genes": {
                    "speed": c.genome.speed,
                    "sense": c.genome.sense,
                    "mass": c.genome.mass,
                    "metabolism": c.genome.metabolism,
                    "mut_rate": c.genome.mut_rate,
                    "major_mut_rate": c.genome.major_mut_rate,
                    "divide_chance": c.genome.divide_chance,
                    "diet": c.genome.diet,
                    "interact": c.genome.interact,
                    "dmg_phot": c.genome.dmg_phot,
                    "dmg_zoop": c.genome.dmg_zoop,
                    "dmg_poly": c.genome.dmg_poly,
                    "lifespan_ticks": c.genome.lifespan_ticks,
                },
            }
        )
    locked_json_write(SAVE_FILE, data)


def load_saved_cells():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []
