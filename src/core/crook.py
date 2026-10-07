"""
Crook geometry for Shape Studio - limb detection

A limb is a stretch of polygon where the shape stays narrow over a
distance: two roughly parallel sides facing each other across the interior.
The crook operation bends a limb at a knee near its center.

Limb detection:
    1. Sample points at regular spacing along the outline.
    2. From each sample, cast a ray along the inward edge normal; the first
       edge hit gives the cross-section chord. Keep it only if it meets the
       far edge roughly perpendicularly.
    3. Group consecutive valid chords into runs while the width changes
       smoothly (tapers are allowed, sudden jumps end the run) and the far
       end tracks along the opposite side.
    4. A run is a limb if its length is at least limb_ratio x its width.
       Each limb is found from both sides; the duplicate is dropped.
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple

Point = Tuple[float, float]


@dataclass
class Chord:
    """A cross-section of the polygon interior from one side to the other."""
    start: Point          # Sample point on the outline
    end: Point            # Where the inward ray meets the opposite side
    start_edge: int       # Edge index containing start
    end_edge: int         # Edge index containing end
    start_arc: float      # Arc-length position of start along the outline
    end_arc: float        # Arc-length position of end along the outline
    width: float          # Chord length


@dataclass
class Limb:
    """A narrow run of the polygon, described by its cross-section chords."""
    chords: List[Chord] = field(default_factory=list)
    width: float = 0.0    # Median chord width
    length: float = 0.0   # Mean of the run's extent along both sides

    @property
    def ratio(self):
        return self.length / self.width if self.width > 0 else 0.0

    def center_chord(self, jitter=0.0, rng=None):
        """Chord near the middle of the limb.

        Args:
            jitter: Max random offset from center, as fraction of chord count
            rng: random.Random-like source (required when jitter > 0)
        """
        n = len(self.chords)
        mid = (n - 1) / 2
        if jitter > 0 and rng is not None:
            mid += rng.uniform(-jitter, jitter) * n
        idx = min(max(int(round(mid)), 0), n - 1)
        return self.chords[idx]


def _signed_area(points):
    n = len(points)
    return sum(points[i][0] * points[(i + 1) % n][1] -
               points[(i + 1) % n][0] * points[i][1] for i in range(n)) / 2


def _ray_hit(origin, direction, points, skip_edge):
    """First edge hit by a ray, excluding skip_edge.

    Returns:
        (distance, hit_point, edge_index, edge_t) or None
    """
    ox, oy = origin
    dx, dy = direction
    n = len(points)
    best = None
    for i in range(n):
        if i == skip_edge:
            continue
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-12:
            continue
        # origin + t*dir = a + u*e
        wx, wy = ax - ox, ay - oy
        t = (wx * ey - wy * ex) / denom
        u = (wx * dy - wy * dx) / denom
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9:
            if best is None or t < best[0]:
                best = (t, (ox + t * dx, oy + t * dy), i, u)
    return best


def _arc_dist(a, b, perimeter):
    """Shortest distance between two arc positions on a closed outline."""
    d = abs(a - b) % perimeter
    return min(d, perimeter - d)


def sample_chords(points, spacing=None, perp_tolerance_deg=30.0):
    """Sample the outline and compute an interior chord at each sample.

    Args:
        points: Polygon vertices
        spacing: Sample spacing in pixels (default: perimeter / 600, min 2)
        perp_tolerance_deg: Max deviation from perpendicular where the
                            chord meets the opposite edge

    Returns:
        (samples, perimeter, spacing) where samples is a list of Chord or
        None (no valid chord at that sample), in outline order
    """
    n = len(points)
    edge_lengths = [math.dist(points[i], points[(i + 1) % n]) for i in range(n)]
    perimeter = sum(edge_lengths)
    if perimeter == 0:
        return [], 0.0, 0.0
    if spacing is None:
        spacing = max(2.0, perimeter / 600)

    # Interior lies to the left of each edge for positive signed area
    inward_sign = 1.0 if _signed_area(points) > 0 else -1.0
    cos_tol = math.cos(math.radians(perp_tolerance_deg))

    edge_starts = []
    acc = 0.0
    for length in edge_lengths:
        edge_starts.append(acc)
        acc += length

    samples = []
    s = spacing / 2
    edge = 0
    while s < perimeter:
        while edge < n - 1 and s >= edge_starts[edge] + edge_lengths[edge]:
            edge += 1
        length = edge_lengths[edge]
        if length == 0:
            s += spacing
            continue
        t = (s - edge_starts[edge]) / length
        ax, ay = points[edge]
        bx, by = points[(edge + 1) % n]
        origin = (ax + t * (bx - ax), ay + t * (by - ay))
        ux, uy = (bx - ax) / length, (by - ay) / length
        normal = (-uy * inward_sign, ux * inward_sign)

        chord = None
        hit = _ray_hit(origin, normal, points, edge)
        if hit is not None:
            dist, hit_point, hit_edge, hit_t = hit
            hx0, hy0 = points[hit_edge]
            hx1, hy1 = points[(hit_edge + 1) % n]
            hlen = edge_lengths[hit_edge]
            if hlen > 0:
                # |cos| between ray and far edge's normal == |sin| between ray and edge
                cross = abs(normal[0] * (hy1 - hy0) - normal[1] * (hx1 - hx0)) / hlen
                if cross >= cos_tol:
                    chord = Chord(
                        start=origin, end=hit_point,
                        start_edge=edge, end_edge=hit_edge,
                        start_arc=s, end_arc=edge_starts[hit_edge] + hit_t * hlen,
                        width=dist,
                    )
        samples.append(chord)
        s += spacing

    return samples, perimeter, spacing


def find_limbs(points, min_width=20.0, limb_ratio=3.0, taper_max=0.6,
               corner_jump_max=0.4, width_tolerance=3.0, max_gap=0.5,
               perp_tolerance_deg=30.0, spacing=None):
    """Find limbs - narrow runs of consistent width - in a polygon.

    Args:
        points: Polygon vertices
        min_width: Ignore runs narrower than this (pixels)
        limb_ratio: Minimum run length / width to qualify as a limb
        taper_max: Max width change per pixel of run length between
                   neighboring chords (0.6 ~ sides diverging ~30 degrees)
        corner_jump_max: Max width step, as a fraction of width, where the
                         run crosses a vertex on its own side
        width_tolerance: Max ratio of widest to narrowest chord in a run
        max_gap: Longest stretch without a valid chord a run may bridge,
                 as a fraction of the run's width (absorbs jagged edges)
        perp_tolerance_deg: See sample_chords
        spacing: See sample_chords

    Returns:
        List of Limb, longest ratio first
    """
    if len(points) < 3:
        return []

    samples, perimeter, spacing = sample_chords(points, spacing, perp_tolerance_deg)
    if not samples:
        return []

    # Start the scan at an invalid sample so runs don't wrap past index 0
    start = next((i for i, c in enumerate(samples) if c is None), 0)
    ordered = samples[start:] + samples[:start]

    runs = []
    current = []
    gap = 0.0

    def close_run():
        if current:
            runs.append(list(current))

    for chord in ordered:
        if chord is None:
            gap += spacing
            if current:
                ref_width = sorted(c.width for c in current)[len(current) // 2]
                if gap > max_gap * ref_width:
                    close_run()
                    current = []
            continue

        if current:
            prev = current[-1]
            run_step = gap + spacing
            change = abs(chord.width - prev.width)
            if chord.start_edge != prev.start_edge:
                # Crossing a vertex on the near side swings the chord, so the
                # width steps rather than tapers; allow a moderate step
                smooth = change <= corner_jump_max * prev.width + taper_max * run_step
            else:
                smooth = change <= taper_max * run_step + 1.0
            widths = [c.width for c in current] + [chord.width]
            consistent = smooth and max(widths) / min(widths) <= width_tolerance
            # Far end must track along the opposite side, not jump elsewhere
            step = _arc_dist(chord.end_arc, prev.end_arc, perimeter)
            tracking = step <= gap + spacing + 0.5 * chord.width
            if not (consistent and tracking):
                close_run()
                current = []
        current.append(chord)
        gap = 0.0
    close_run()

    limbs = []
    for run in runs:
        widths = sorted(c.width for c in run)
        width = widths[len(widths) // 2]
        if width < min_width or len(run) < 2:
            continue
        near_len = _arc_dist(run[0].start_arc, run[-1].start_arc, perimeter)
        far_len = _arc_dist(run[0].end_arc, run[-1].end_arc, perimeter)
        length = (near_len + far_len) / 2
        if length < limb_ratio * width:
            continue
        limbs.append(Limb(chords=run, width=width, length=length))

    limbs.sort(key=lambda l: l.ratio, reverse=True)
    return _dedupe(limbs, perimeter)


def _dedupe(limbs, perimeter):
    """Drop limbs that are the same structure seen from the opposite side."""
    kept = []
    for limb in limbs:
        near = [c.start_arc for c in limb.chords]
        duplicate = False
        for other in kept:
            # This limb's near side lies along the other's far side
            other_far = [c.end_arc for c in other.chords]
            hits = sum(
                1 for a in near
                if min(_arc_dist(a, b, perimeter) for b in other_far) <= other.width * 0.5
            )
            if hits >= len(near) * 0.5:
                duplicate = True
                break
        if not duplicate:
            kept.append(limb)
    return kept
