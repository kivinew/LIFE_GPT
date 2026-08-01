# memory.py — Experience memory and class-learning for LIFE_GPT cells
# Each cell keeps a compact dict of observed classes and learned scores.

__all__ = ["CellMemory"]

# -- Tiny record type (avoids full dataclass overhead) -------------------
class MemorySlot:
    """One entry: what a cell remembers about another appearance class."""
    __slots__ = ("threat", "coop", "n_encounters")

    def __init__(self):
        self.threat = 0.0       # 0..1   higher → more dangerous
        self.coop   = 0.0       # 0..1   higher → better to cooperate
        self.n_encounters = 0   # total interactions with this class

    def decay(self, factor: float):
        self.threat *= factor
        self.coop   *= factor


class CellMemory:
    """
    Lightweight associative memory keyed on the opponent's *appearance* class
    (cls hash).  Updated during combat and social events; consulted when
    deciding whether to flee, attack, or cooperate.
    """

    def __init__(self, max_slots: int = 20):
        self._slots: dict[int, MemorySlot] = {}
        self._max = max_slots
        self._tick = 0

    # ── queries ────────────────────────────────────────────────
    def threat(self, cls: int) -> float:
        s = self._slots.get(cls)
        return s.threat if s else 0.0

    def coop(self, cls: int) -> float:
        s = self._slots.get(cls)
        return s.coop if s else 0.0

    def get_slot(self, cls: int) -> MemorySlot:
        """Return or create a slot, enforcing the slot cap."""
        slot = self._slots.get(cls)
        if slot is not None:
            return slot
        # enforce cap — evict oldest (lowest encounter count)
        if len(self._slots) >= self._max:
            self._evict_one()
        slot = MemorySlot()
        self._slots[cls] = slot
        return slot

    # ── updates ────────────────────────────────────────────────
    def record_threat(self, cls: int, magnitude: float = 1.0):
        """Called when hurt by or witnessing aggression from cls."""
        s = self.get_slot(cls)
        s.threat = min(1.0, s.threat + magnitude * 0.1)
        s.n_encounters += 1

    def record_cooperation(self, cls: int, magnitude: float = 1.0):
        """Called when receiving or giving help to/from cls."""
        s = self.get_slot(cls)
        s.coop = min(1.0, s.coop + magnitude * 0.1)
        s.n_encounters += 1

    def record_neutral(self, cls: int):
        """Called on a harmless encounter."""
        s = self.get_slot(cls)
        s.n_encounters += 1

    # ── periodic decay ─────────────────────────────────────────
    def tick(self, every_n: int = 500):
        """Halve scores every `every_n` ticks so old experiences fade."""
        self._tick += 1
        if self._tick % every_n == 0:
            for s in self._slots.values():
                s.decay(0.5)

    # ── internal helpers ───────────────────────────────────────
    def _evict_one(self):
        """Remove the slot with the fewest encounters."""
        if not self._slots:
            return
        weakest = min(self._slots, key=lambda c: self._slots[c].n_encounters)
        del self._slots[weakest]

    def clone(self) -> "CellMemory":
        """Create an independent copy for offspring."""
        new_mem = CellMemory(max_slots=self._max)
        for cls, slot in self._slots.items():
            new_slot = MemorySlot()
            new_slot.threat = slot.threat
            new_slot.coop = slot.coop
            new_slot.n_encounters = slot.n_encounters
            new_mem._slots[cls] = new_slot
        return new_mem

    def __len__(self):
        return len(self._slots)

    def summary(self) -> dict:
        """Return {cls: (threat, coop, n)} for debugging / UI."""
        return {c: (s.threat, s.coop, s.n_encounters)
                for c, s in self._slots.items()}