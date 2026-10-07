"""
Crook geometry for Shape Studio - limb detection and knee bend

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

Knee bend (bend_at_chord):
    1. Insert both chord ends into the outline. The chord splits the
       polygon into two pieces; the smaller (by area) is the limb.
    2. One chord end is the pivot P - the inside corner of the bend. The
       limb rotates about P, swinging toward P's side.
    3. On the outside of the bend, the body's edge and the rotated limb's
       edge are extended to meet at a sharp corner O, which replaces the
       other chord end. Limb width is preserved on both arms.
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


def find_limbs(points, min_width=20.0, limb_ratio=3.0, min_length=0.0,
               taper_max=0.6, corner_jump_max=0.4, width_tolerance=3.0,
               max_gap=0.5, perp_tolerance_deg=30.0, spacing=None):
    """Find limbs - narrow runs of consistent width - in a polygon.

    Args:
        points: Polygon vertices
        min_width: Ignore runs narrower than this (pixels)
        min_length: Ignore runs shorter than this (pixels), whatever their
                    ratio - keeps small teeth from counting as limbs
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
        if length < limb_ratio * width or length < min_length:
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


def _split_at_chord(points, chord, snap=1.0):
    """Insert the chord's ends into the outline.

    A chord end within snap pixels of an existing vertex uses that vertex.

    Returns:
        (outline, start_index, end_index)
    """
    n = len(points)
    vertex_of = {}
    on_edge = {}
    for key, edge, pt in (('start', chord.start_edge, chord.start),
                          ('end', chord.end_edge, chord.end)):
        a, b = points[edge], points[(edge + 1) % n]
        if math.dist(a, pt) <= snap:
            vertex_of[key] = edge
        elif math.dist(b, pt) <= snap:
            vertex_of[key] = (edge + 1) % n
        else:
            on_edge[edge] = (key, pt)

    outline = []
    index = {}
    for i, v in enumerate(points):
        for key, vi in vertex_of.items():
            if vi == i:
                index[key] = len(outline)
        outline.append(v)
        if i in on_edge:
            key, pt = on_edge[i]
            index[key] = len(outline)
            outline.append(pt)

    if index['start'] == index['end']:
        raise ValueError("Crook chord is degenerate")
    return outline, index['start'], index['end']


def _chain(outline, i, j):
    """Outline points walking forward from index i to index j inclusive."""
    m = len(outline)
    out = [outline[i]]
    k = i
    while k != j:
        k = (k + 1) % m
        out.append(outline[k])
    return out


def _rotate(point, center, cos_a, sin_a):
    x, y = point[0] - center[0], point[1] - center[1]
    return (center[0] + x * cos_a - y * sin_a, center[1] + x * sin_a + y * cos_a)


def _line_intersection(p, d, q, e):
    """Intersection of lines p + t*d and q + s*e.

    Returns:
        (point, t, s) or None if parallel
    """
    denom = d[0] * e[1] - d[1] * e[0]
    if abs(denom) < 1e-9:
        return None
    wx, wy = q[0] - p[0], q[1] - p[1]
    t = (wx * e[1] - wy * e[0]) / denom
    s = (wx * d[1] - wy * d[0]) / denom
    return (p[0] + t * d[0], p[1] + t * d[1]), t, s


def bend_at_chord(points, chord, angle_deg, pivot='start', max_mitre=3.0):
    """Bend the polygon at a chord into a knee.

    Args:
        points: Polygon vertices
        chord: Chord to bend at (typically Limb.center_chord())
        angle_deg: Bend angle in degrees (> 0)
        pivot: 'start' or 'end' - which chord end is the inside corner
        max_mitre: Reject if the outside corner lies further than this
                   many chord widths from the chord

    Returns:
        (new_points, moved) where moved maps each original limb vertex to
        its rotated position (unrounded)

    Raises:
        ValueError: If the bend cannot be constructed
    """
    outline, i_start, i_end = _split_at_chord(points, chord)

    # The smaller piece is the limb and rotates; the body stays put
    piece_a = _chain(outline, i_start, i_end)
    piece_b = _chain(outline, i_end, i_start)
    if abs(_signed_area(piece_a)) <= abs(_signed_area(piece_b)):
        limb, body = piece_a, piece_b
    else:
        limb, body = piece_b, piece_a
    # body runs X..Y and limb runs Y..X, where {X, Y} are the chord ends
    if len(limb) < 3:
        raise ValueError("Crook limb has no vertices to rotate")

    p = outline[i_start] if pivot == 'start' else outline[i_end]
    q = outline[i_end] if pivot == 'start' else outline[i_start]
    width = math.dist(p, q)
    if width == 0:
        raise ValueError("Crook chord has zero width")

    # Unit vector across the chord (P -> Q) and into the limb
    vx, vy = (q[0] - p[0]) / width, (q[1] - p[1]) / width
    ux, uy = -vy, vx
    cx = sum(pt[0] for pt in limb) / len(limb)
    cy = sum(pt[1] for pt in limb) / len(limb)
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    if ux * (cx - mx) + uy * (cy - my) < 0:
        ux, uy = -ux, -uy

    # Rotate so the limb swings toward P's side: u turns toward -v
    angle = math.radians(angle_deg)
    if (-uy) * (-vx) + ux * (-vy) < 0:
        angle = -angle
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    interior = limb[1:-1]
    rotated = [_rotate(pt, p, cos_a, sin_a) for pt in interior]
    moved = dict(zip(interior, rotated))

    # Outside corner: extend the body edge into Q and the rotated limb
    # edge out of Q' until they meet
    q_rot = _rotate(q, p, cos_a, sin_a)
    if body[-1] == q:
        body_nb, limb_nb = body[-2], rotated[0]
    else:
        body_nb, limb_nb = body[1], rotated[-1]
    d_body = (q[0] - body_nb[0], q[1] - body_nb[1])
    d_limb = (q_rot[0] - limb_nb[0], q_rot[1] - limb_nb[1])
    hit = _line_intersection(q, d_body, q_rot, d_limb)
    if hit is None:
        raise ValueError("Crook outside edges are parallel")
    corner, t, s = hit
    if t < 0 or s < 0:
        raise ValueError("Crook outside corner falls behind the knee")
    if math.dist(corner, q) > max_mitre * width:
        raise ValueError("Crook outside corner too far from the knee")

    if body[-1] == q:
        new_points = body[:-1] + [corner] + rotated
    else:
        new_points = [corner] + body[1:] + rotated
    return new_points, moved
