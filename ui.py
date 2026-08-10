# UI component classes for LIFE_GPT
import pygame
from config import (
    DARK,
    BLUE,
    WHITE,
    GRAY,
    RED,
    TEAL,
    YEL,
    SEASON_LENGTH,
    SEASON_ORDER,
    tr,
)
from cell import diet_color
import math
from collections import deque

_SEASON_COLOR = {
    "spring": (90, 200, 110),
    "summer": (230, 210, 80),
    "autumn": (220, 140, 60),
    "winter": (100, 150, 230),
}


class VBox:
    def __init__(self, x, y, width, spacing=28):
        self.x = x
        self.y = y
        self.width = width
        self.spacing = spacing

    def add(self, height=20):
        rect = (self.x, self.y, self.width)
        self.y += height + self.spacing
        return rect

    def skip(self, pixels):
        self.y += pixels


class Slider:
    def __init__(self, x, y, w, lab, mn, mx, val, labels=None, unit=None):
        self.rect = pygame.Rect(x, y, w, 20)
        self.lab, self.mn, self.mx, self.val = lab, mn, mx, val
        self.labels = labels
        self.unit = unit
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        if self.unit:
            text_str = f"{self.lab}: {self.val:.0f}{self.unit}"
        else:
            text_str = f"{self.lab}: {self.val:.2f}"
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        surf.blit(self._cached_text, (self.rect.x, self.rect.y - 12))
        pygame.draw.rect(
            surf, DARK, (self.rect.x, self.rect.y + 3, self.rect.w, 6), 0, 3
        )
        fw = int((self.val - self.mn) / (self.mx - self.mn) * self.rect.w)
        pygame.draw.rect(surf, BLUE, (self.rect.x, self.rect.y + 3, fw, 6), 0, 3)
        if self.labels and len(self.labels) > 1:
            n = len(self.labels)
            for i in range(n):
                lx = self.rect.x + int(i * self.rect.w / (n - 1))
                ly = self.rect.y + 11
                tick_col = (
                    BLUE
                    if self.val >= self.mn + i * (self.mx - self.mn) / (n - 1)
                    and self.val < self.mn + (i + 1) * (self.mx - self.mn) / (n - 1)
                    else GRAY
                )
                pygame.draw.line(surf, tick_col, (lx, ly - 1), (lx, ly + 1), 1)
                lt = font.render(self.labels[i], True, tick_col)
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))

    def handle(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.val = max(
                self.mn,
                min(
                    self.mx,
                    self.mn
                    + (event.pos[0] - self.rect.x) / self.rect.w * (self.mx - self.mn),
                ),
            )
            self.drag = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        if event.type == pygame.MOUSEMOTION and self.drag:
            self.val = max(
                self.mn,
                min(
                    self.mx,
                    self.mn
                    + (event.pos[0] - self.rect.x) / self.rect.w * (self.mx - self.mn),
                ),
            )
class SliderInt:
    def __init__(self, x, y, w, lab, mn, mx, val, labels=None):
        self.rect = pygame.Rect(x, y, w, 20)
        self.lab = lab
        self.mn, self.mx = mn, mx
        self.val = int(val)
        self.labels = labels
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        current_label = self.labels[int(self.val)] if self.labels else str(self.val)
        text_str = f"{self.lab}: {current_label}"
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        surf.blit(self._cached_text, (self.rect.x, self.rect.y - 12))
        pygame.draw.rect(
            surf, DARK, (self.rect.x, self.rect.y + 3, self.rect.w, 6), 0, 3
        )
        fw = (
            int((self.val - self.mn) / (self.mx - self.mn) * self.rect.w)
            if self.mx > self.mn
            else 0
        )
        pygame.draw.rect(surf, BLUE, (self.rect.x, self.rect.y + 3, fw, 6), 0, 3)
        if self.labels and len(self.labels) > 0:
            n = len(self.labels)
            for i in range(n):
                lx = (
                    self.rect.x + int(i * self.rect.w / (n - 1))
                    if n > 1
                    else self.rect.x
                )
                ly = self.rect.y + 11
                tick_col = BLUE if i == int(self.val) else GRAY
                pygame.draw.line(surf, tick_col, (lx, ly - 1), (lx, ly + 1), 1)
                lt = font.render(self.labels[i], True, tick_col)
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))

    def handle(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            n = len(self.labels) if self.labels else (self.mx - self.mn + 1)
            idx = (
                int((event.pos[0] - self.rect.x) / self.rect.w * (n - 1))
                if n > 1
                else 0
            )
            self.val = max(self.mn, min(self.mx, idx))
            self.drag = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        if event.type == pygame.MOUSEMOTION and self.drag:
            n = len(self.labels) if self.labels else (self.mx - self.mn + 1)
            idx = (
                int((event.pos[0] - self.rect.x) / self.rect.w * (n - 1))
                if n > 1
                else 0
            )
            self.val = max(self.mn, min(self.mx, idx))
class Toggle:
    def __init__(self, x, y, w, h, labels, val=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.labels, self.val = labels, val
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        text_str = self.labels[self.val]
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        pygame.draw.rect(surf, DARK, self.rect, 0, 4)
        pygame.draw.rect(surf, BLUE, self.rect, 1, 4)
        surf.blit(
            self._cached_text,
            (
                self.rect.centerx - self._cached_text.get_width() // 2,
                self.rect.centery - self._cached_text.get_height() // 2,
            ),
        )

    def handle(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        ):
            self.val = (self.val + 1) % len(self.labels)

class PopulationGraph:
    """
    Population graph tracking counts per cell class over time (tick-based).
    Seasons are shown as tinted background bands with labels. Line colors
    match the cell diet colors. A YEL line shows the total.
    A sample is recorded every `sample_interval` ticks; the visible history
    spans `history_length` ticks (independent of frame rate / time scale).
    """

    def __init__(self, history_length=10000, sample_interval=10):
        self.history_length = history_length
        self.sample_interval = sample_interval
        self.history = deque()  # of (tick, counts)
        self.cls_diet = {}  # cls -> diet, to color lines like the cells
        # Per-class visibility (default: visible). Populated lazily in update()/draw().
        self.cls_visible = {}
        # Toggle for the aggregated "total" line.
        self.show_total = True
        # Vertical scroll offset (index) for the legend palette of classes.
        self.legend_offset = 0
        self._next_sample = 0
        # Кэш отрендеренной поверхности графика
        self._cached_surf = None
        self._cache_key = None
        self._cache_version = 0

    def _ensure_cls(self, cls):
        if cls not in self.cls_visible:
            self.cls_visible[cls] = True
            self._cache_version += 1

    def _class_color(self, cls):
        seed = cls if isinstance(cls, int) else abs(hash(cls)) % 1000
        return diet_color(self.cls_diet.get(cls, 0), seed)

    def toggle_cls(self, cls):
        self.cls_visible[cls] = not self.cls_visible.get(cls, True)
        self._cache_version += 1

    def toggle_diet(self, diet):
        """Toggle visibility of every class whose diet matches."""
        changed = False
        for cls, dd in self.cls_diet.items():
            if dd == diet:
                self.cls_visible[cls] = not self.cls_visible.get(cls, True)
                changed = True
        if changed:
            self._cache_version += 1
        return changed

    def toggle_total(self):
        self.show_total = not self.show_total
        self._cache_version += 1

    def legend_entries(self):
        """Return (cls, color, visible) for every known class, sorted by cls."""
        out = []
        for cls in sorted(self.cls_diet.keys(), key=lambda k: (str(k))):
            self._ensure_cls(cls)
            out.append((cls, self._class_color(cls), self.cls_visible[cls]))
        return out

    def update(self, tick, cells):
        """Call each tick to record the current population counts per class."""
        if tick < self._next_sample:
            return
        self._next_sample = tick + self.sample_interval
        counts = {}
        for c in cells:
            if c.energy > 0:  # only count living cells
                cls = c.cls
                counts[cls] = counts.get(cls, 0) + 1
                self.cls_diet[cls] = c.genome.diet
                self._ensure_cls(cls)
        self.history.append((tick, counts))
        self._cache_version += 1
        while (
            len(self.history) > 2 and (tick - self.history[0][0]) > self.history_length
        ):
            self.history.popleft()

    def draw(self, surf, x, y, width, height):
        """Draw the graph onto the surface at (x, y) with given width and height.

        Кэширует отрендеренную поверхность: перерисовывает только при изменении
        данных или видимости классов (инвалидация через _cache_version).
        """
        if len(self.history) < 2:
            return  # not enough data

        label_w = 30  # leeway for Y-axis tick labels drawn left of the graph
        cache_key = (self._cache_version, width, height)
        if self._cached_surf is not None and self._cache_key == cache_key:
            surf.blit(self._cached_surf, (x - label_w, y))
            return

        # Рендерим в локальную поверхность (label_w + width пикселей)
        cw = width + label_w
        graph_surf = pygame.Surface((cw, height), pygame.SRCALPHA)

        history_list = list(self.history)
        t0 = history_list[0][0]
        t1 = history_list[-1][0]
        span = max(1, t1 - t0)

        def px_x(t):
            return label_w + 5 + (t - t0) / span * (width - 10)

        # Background
        bg_rect = pygame.Rect(label_w, 0, width, height)
        pygame.draw.rect(graph_surf, DARK, bg_rect)

        # Season bands (tinted background + label per season)
        band = pygame.Surface((cw, height), pygame.SRCALPHA)
        start_k = max(0, t0 // SEASON_LENGTH)
        end_k = t1 // SEASON_LENGTH
        for k in range(start_k, end_k + 1):
            season = SEASON_ORDER[k % len(SEASON_ORDER)]
            bx0 = px_x(max(k * SEASON_LENGTH, t0))
            bx1 = px_x(min((k + 1) * SEASON_LENGTH, t1))
            if bx1 <= bx0:
                continue
            band.fill((*_SEASON_COLOR[season], 40), (bx0, 0, bx1 - bx0, height))
            if bx1 - bx0 >= 40:
                font = pygame.font.Font(None, 14)
                label = font.render(tr(season), True, WHITE)
                band.blit(label, (bx0 + 3, 3))
        graph_surf.blit(band, (0, 0))
        pygame.draw.rect(graph_surf, GRAY, bg_rect, 1)

        classes = set()
        max_count = 0
        for _, frame in history_list:
            classes.update(frame.keys())
            frame_total = sum(frame.values())
            # Max must cover both single-class peaks AND the total line
            if frame_total > max_count:
                max_count = frame_total
            for val in frame.values():
                if val > max_count:
                    max_count = val
            for cls in frame.keys():
                self._ensure_cls(cls)
        if max_count == 0:
            max_count = 1  # avoid division by zero

        # Scale factor for y: value -> pixel offset from bottom
        def scale_y(val):
            return height - (val / max_count) * (height - 10)  # 5px margin top/bottom

        # Draw one line per cell class, colors matching cell colors
        for cls in sorted(classes, key=lambda k: str(k)):
            if not self.cls_visible.get(cls, True):
                continue  # toggled off in the legend
            color = self._class_color(cls)
            points = [
                (px_x(tick), scale_y(frame.get(cls, 0))) for tick, frame in history_list
            ]
            if len(points) > 1:
                pygame.draw.lines(graph_surf, color, False, points, 2)

        # Total population line
        total_points = [
            (px_x(tick), scale_y(sum(frame.values()))) for tick, frame in history_list
        ]
        if self.show_total and len(total_points) > 1:
            pygame.draw.lines(graph_surf, YEL, False, total_points, 2)

        # Draw axes
        # X axis
        pygame.draw.line(
            graph_surf, GRAY, (label_w + 5, height - 5), (label_w + width - 5, height - 5), 1
        )
        # Y axis
        pygame.draw.line(graph_surf, GRAY, (label_w + 5, 5), (label_w + 5, height - 5), 1)

        # Optional: draw ticks on Y axis
        for i in range(1, 5):
            val = (i / 4) * max_count
            py = height - (i / 4) * (height - 10)
            pygame.draw.line(graph_surf, GRAY, (label_w + 5, py), (label_w + 8, py), 1)
            font = pygame.font.Font(None, 14)
            text = font.render(f"{int(val)}", True, WHITE)
            graph_surf.blit(text, (0, py - 7))

        # Кэшируем и blit
        self._cached_surf = graph_surf
        self._cache_key = cache_key
        surf.blit(graph_surf, (x - label_w, y))


# End of file
