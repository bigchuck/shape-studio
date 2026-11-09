"""
Rigid geometry for Shape Studio - polygon edges on a fixed set of directions

RIGID makes every edge of a polygon run along one of a few allowed
directions. An edge that is off-direction becomes an elbow: two legs along
the two allowed headings on either side of it, meeting at a new corner. The
original vertices stay where they are. With several steps per edge the
elbows form a staircase along the old edge.

Directions are lines (0 also means 180). 0 is always one of them; the rest
come from a preset, an explicit list, or are drawn at random. TILT turns the
whole set.

Any vector splits uniquely into two non-parallel directions, so the two
directions do not have to be at right angles.

Elbow sides:
    out  - the corner adds material (outer outline bulges, holes shrink)
    in   - the corner removes material
    alt  - alternates from one rigid edge to the next
A weighted out/in mix picks a side for each edge.

Safety: when a corner makes the outline cross itself (or a hole), only
the step involved is fixed, in order: flip its corner to the other side,
then split it into two shallower steps (up to max_splits times), then
leave that piece at its original angle. Pieces left at their original
angle are always safe because the original polygon was valid, so the
fixing always ends.
"""
import math

from src.core.hollow import _segments_cross, point_in_ring

PRESETS = {
    'ortho': [90.0],
    'hex': [60.0, 120.0],
    'octo': [45.0, 90.0, 135.0],
}


# ---------------------------------------------------------------------------
# Value parsing (shared by the parser and config defaults)
# ---------------------------------------------------------------------------

def parse_dirs(value):
    """DIRS value -> preset name, 'random', or list of angles.

    Angles may be separated by ',' or '/' (the slash form survives inline
    weighted strings in templates). A written-out 0 is allowed.
    """
    if isinstance(value, (list, tuple)):
        return [float(a) for a in value]
    text = str(value).strip()
    key = text.lower()
    if key in PRESETS or key == 'random':
        return key
    try:
        return [float(a) for a in text.replace('/', ',').split(',') if a.strip()]
    except ValueError:
        raise ValueError(
            f"RIGID DIRS must be ortho, hex, octo, random or angles like 70 or 50,110 - got '{value}'"
        )


def parse_elbow(value):
    """ELBOW value -> 'alt' or [[side, weight], ...] with sides out/in."""
    from src.core.param_converters import convert_weighted_list
    if isinstance(value, str) and value.strip().lower() == 'alt':
        return 'alt'
    text = value.lower() if isinstance(value, str) else value
    try:
        weighted = convert_weighted_list(text, choices=['out', 'in'])
    except ValueError:
        raise ValueError(f"RIGID ELBOW must be out, in, alt or weights like out:3,in:1 - got '{value}'")
    if sum(w for _, w in weighted) <= 0:
        raise ValueError("RIGID ELBOW weights must not all be 0")
    return weighted


# ---------------------------------------------------------------------------
# Directions
# ---------------------------------------------------------------------------

def _line_gap(a, b):
    """Angle between two lines (degrees, 0-90)."""
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def random_dirs(count, sep, rng):
    """Draw `count` whole-degree directions in 1..179, all at least `sep`
    degrees (as lines) from each other and from 0.

    The count + 1 lines (with 0) split the 180-degree half turn into
    count + 1 gaps. Each gap gets the minimum `sep`, and the spare degrees
    are shared out at random. This closely matches drawing uniformly and
    rejecting sets that are too close, but never needs a retry.
    """
    gap = max(1, math.ceil(sep))
    spare = 180 - (count + 1) * gap
    if spare < 0:
        raise ValueError(
            f"RIGID: cannot fit {count} random directions plus 0 at least "
            f"{sep:g} degrees apart (config rigid.sep)"
        )
    cuts = sorted(rng.randint(0, spare) for _ in range(count))
    return [float((k + 1) * gap + cuts[k]) for k in range(count)]


def resolve_dirs(spec, count_min, count_max, sep, rng):
    """Turn a DIRS spec into the sorted list of directions (0 included).

    Args:
        spec: 'ortho' | 'hex' | 'octo' | 'random' | list of numbers
        count_min, count_max: number of random directions (besides 0)
        sep: minimum separation for random directions (degrees)
        rng: random module or Random instance

    Returns:
        Sorted list of distinct line angles in [0, 180), starting with 0
    """
    if isinstance(spec, str):
        key = spec.lower()
        if key == 'random':
            others = random_dirs(rng.randint(count_min, count_max), sep, rng)
        elif key in PRESETS:
            others = PRESETS[key]
        else:
            raise ValueError(f"RIGID: unknown DIRS '{spec}' (use ortho, hex, octo, random or angles)")
    else:
        others = list(spec)

    dirs = [0.0]
    for a in others:
        a = float(a) % 180.0
        if all(_line_gap(a, b) > 1e-6 for b in dirs):
            dirs.append(a)
    if len(dirs) < 2:
        raise ValueError("RIGID: DIRS needs at least one direction besides 0 (0 is always included)")
    return sorted(dirs)


def headings(dirs, tilt):
    """Sorted headings (degrees, 0-360) for the tilted direction lines."""
    hs = set()
    for d in dirs:
        a = (d + tilt) % 180.0
        hs.add(round(a, 9))
        hs.add(round(a + 180.0, 9))
    return sorted(hs)


def _bracket(theta, hs):
    """Headings on either side of edge angle theta.

    Returns:
        (h1, h2, d1, d2): lower and upper heading, and theta's distance
        from each (degrees)
    """
    n = len(hs)
    for i in range(n):
        lo = hs[i]
        hi = hs[i + 1] if i + 1 < n else hs[0] + 360.0
        t = theta if theta >= lo else theta + 360.0
        if lo <= t < hi:
            return lo, hi % 360.0, t - lo, hi - t
    return hs[-1], hs[0], 0.0, 360.0  # unreachable for theta in [0, 360)


def _unit(deg):
    r = math.radians(deg)
    return math.cos(r), math.sin(r)


# ---------------------------------------------------------------------------
# Edge plans
# ---------------------------------------------------------------------------

def signed_area(ring):
    n = len(ring)
    return sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
               for i in range(n)) / 2.0


def plan_ring(ring, hs, params, rng, alt_state, ring_index, counts):
    """Decide what happens to each edge of a ring.

    Returns:
        List with one entry per edge: None (edge kept as is) or a plan
        {'h': (h1, h2), 'planned_out': bool, 'units': [unit, ...]}.
        Each unit is one step of the staircase over the fraction t0..t1
        of the edge, with its own side ('out'), fix level, split depth and
        'free' flag, so a crossing fix changes only the step involved.
    """
    plans = []
    n = len(ring)
    tol = params['snap_tolerance']
    for i in range(n):
        p, q = ring[i], ring[(i + 1) % n]
        vx, vy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(vx, vy)
        take = rng.random() < params['edges']
        theta = math.degrees(math.atan2(vy, vx)) % 360.0
        h1, h2, d1, d2 = _bracket(theta, hs)
        if min(d1, d2) < tol:
            counts['aligned'] += 1
            plans.append(None)
            continue
        if not take or length < max(params['min_edge'], 1e-9):
            counts['skipped'] += 1
            plans.append(None)
            continue

        if params['step'] > 0:
            steps = max(1, int(round(length / params['step'])))
        else:
            steps = rng.randint(params['steps_min'], params['steps_max'])

        elbow = params['elbow']
        if elbow == 'alt':
            want_out = alt_state[0] % 2 == 0
            alt_state[0] += 1
        else:
            sides = [s for s, _ in elbow]
            weights = [w for _, w in elbow]
            want_out = rng.choices(sides, weights=weights)[0] == 'out'

        units = [_unit_new((ring_index, i), k / steps, (k + 1) / steps, want_out, 0)
                 for k in range(steps)]
        plans.append({'h': (h1, h2), 'planned_out': want_out, 'units': units})
    return plans


def _unit_new(edge, t0, t1, out, depth):
    return {'edge': edge, 't0': t0, 't1': t1, 'out': out, 'planned_out': out,
            'level': 0, 'depth': depth, 'free': False}


def _edge_points(p, q, plan, material_left):
    """Points and tags for one edge from p (included) up to q (excluded).

    Tags name the unit each segment belongs to (None for an untouched edge).
    """
    if plan is None:
        return [p], [None]
    vx, vy = q[0] - p[0], q[1] - p[1]
    u1, u2 = _unit(plan['h'][0]), _unit(plan['h'][1])
    det = u1[0] * u2[1] - u1[1] * u2[0]

    pts, tags = [], []
    for unit in plan['units']:
        bx, by = p[0] + vx * unit['t0'], p[1] + vy * unit['t0']
        pts.append((bx, by))
        tags.append(unit)
        if unit['free']:
            continue
        f = unit['t1'] - unit['t0']
        sx, sy = vx * f, vy * f
        s = (sx * u2[1] - sy * u2[0]) / det
        t = (u1[0] * sy - u1[1] * sx) / det
        leg1 = (u1[0] * s, u1[1] * s)
        leg2 = (u2[0] * t, u2[1] * t)
        # Corner after leg1 is on the left of the step when cross > 0
        leg1_left = (sx * leg1[1] - sy * leg1[0]) > 0
        leg1_out = leg1_left != material_left
        first = leg1 if unit['out'] == leg1_out else leg2
        pts.append((bx + first[0], by + first[1]))
        tags.append(unit)
    return pts, tags


def build_ring(ring, plans, material_left):
    """Build the rigid ring and a tag (unit or None) per segment."""
    pts, tags = [], []
    n = len(ring)
    for i in range(n):
        e_pts, e_tags = _edge_points(ring[i], ring[(i + 1) % n], plans[i], material_left)
        pts.extend(e_pts)
        tags.extend(e_tags)
    return pts, tags


# ---------------------------------------------------------------------------
# Crossing detection (grid-accelerated)
# ---------------------------------------------------------------------------

def find_crossings(rings, cell=None):
    """Find touching or crossing segments across a set of rings.

    Args:
        rings: list of (points, tags) - tags[i] names the unit that
               made the segment starting at points[i] (None = untouched)

    Returns:
        List of (tag, tag) pairs for segments that touch or cross. Adjacent segments that fold back on each
        other (a zero-width spike) count too.
    """
    segs = []
    pairs = []
    for r, (pts, tags) in enumerate(rings):
        n = len(pts)
        for i in range(n):
            segs.append((r, i, n, pts[i], pts[(i + 1) % n], tags[i]))
        # Fold-backs between neighbours: collinear and pointing back
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            abx, aby = b[0] - a[0], b[1] - a[1]
            bcx, bcy = c[0] - b[0], c[1] - b[1]
            scale = max(math.hypot(abx, aby) * math.hypot(bcx, bcy), 1e-12)
            if abs(abx * bcy - aby * bcx) / scale < 1e-6 and abx * bcx + aby * bcy < 0:
                pairs.append((tags[i - 1], tags[i]))
    if not segs:
        return pairs

    if cell is None:
        total = sum(math.dist(a, b) for _, _, _, a, b, _ in segs)
        cell = max(4.0, 2.0 * total / len(segs))

    grid = {}
    for k, (_, _, _, a, b, _) in enumerate(segs):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for gx in range(int(math.floor(x0 / cell)), int(math.floor(x1 / cell)) + 1):
            for gy in range(int(math.floor(y0 / cell)), int(math.floor(y1 / cell)) + 1):
                grid.setdefault((gx, gy), []).append(k)

    seen = set()
    for bucket in grid.values():
        for ii in range(len(bucket)):
            ka = bucket[ii]
            ra, ia, na, a1, a2, ta = segs[ka]
            for jj in range(ii + 1, len(bucket)):
                kb = bucket[jj]
                pair = (ka, kb) if ka < kb else (kb, ka)
                if pair in seen:
                    continue
                seen.add(pair)
                rb, ib, nb, b1, b2, tb = segs[kb]
                if ra == rb:
                    d = abs(ia - ib)
                    if d == 1 or d == na - 1:
                        continue  # neighbours share an endpoint
                if _segments_cross(a1, a2, b1, b2):
                    pairs.append((ta, tb))
    return pairs


def _repeated_points(pts, tags):
    """Pairs of units that put a point on the same spot."""
    pairs, seen = [], {}
    for i, p in enumerate(pts):
        if p in seen:
            pairs.append((tags[seen[p]], tags[i]))
        seen[p] = i
    return pairs


def merge_collinear(pts, eps=1e-6):
    """Drop points that sit on a straight run (same direction both sides)."""
    res = list(pts)
    changed = True
    while changed and len(res) > 3:
        changed = False
        out = []
        n = len(res)
        for i in range(n):
            a, b, c = res[i - 1], res[i], res[(i + 1) % n]
            abx, aby = b[0] - a[0], b[1] - a[1]
            bcx, bcy = c[0] - b[0], c[1] - b[1]
            cross = abx * bcy - aby * bcx
            dot = abx * bcx + aby * bcy
            scale = max(math.hypot(abx, aby) * math.hypot(bcx, bcy), 1e-12)
            if abs(cross) / scale < eps and dot > 0:
                changed = True
                continue
            out.append(b)
        if changed:
            res = out
    return res


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def _advance(unit, plan, max_splits):
    """Next fix for a unit (one step) that causes a crossing.

    Order: flip the corner to the other side; then split the step into
    two shallower halves (each starts again on the planned side), up to
    max_splits times; then leave this piece of the edge at its original
    angle. Only the step involved changes, not the whole edge.
    """
    if unit['level'] == 0:
        unit['level'] = 1
        unit['out'] = not unit['out']
        return
    if unit['depth'] < max_splits:
        units = plan['units']
        i = next(k for k, u in enumerate(units) if u is unit)
        mid = (unit['t0'] + unit['t1']) / 2
        side = unit['planned_out']
        units[i:i + 1] = [
            _unit_new(unit['edge'], unit['t0'], mid, side, unit['depth'] + 1),
            _unit_new(unit['edge'], mid, unit['t1'], side, unit['depth'] + 1),
        ]
        return
    unit['free'] = True


def rigid_polygon(points, holes, params, rng):
    """Make a polygon's edges run along a fixed set of directions.

    Args:
        points: outer ring
        holes: hole rings (kept as is unless params['holes'])
        params: dict with dirs, count_min, count_max, tilt_min, tilt_max,
                steps_min, steps_max, step, elbow ('alt' or [[side, w], ...]),
                edges, min_edge, holes, sep, snap_tolerance, max_splits
        rng: random module or Random instance

    Returns:
        (outer, holes, info)
    """
    dirs = resolve_dirs(params['dirs'], params['count_min'], params['count_max'],
                        params['sep'], rng)
    if params['tilt_min'] == params['tilt_max']:
        tilt = float(params['tilt_min'])
    else:
        tilt = rng.uniform(params['tilt_min'], params['tilt_max'])
    hs = headings(dirs, tilt)

    rings = [[tuple(map(float, p)) for p in points]]
    rings += [[tuple(map(float, p)) for p in h] for h in holes]

    outer_left = signed_area(rings[0]) > 0
    # Material is inside the outer ring and outside each hole
    material_left = [outer_left] + [signed_area(h) <= 0 for h in rings[1:]]

    alt_state = [0]
    counts = {'aligned': 0, 'skipped': 0}
    plans = [plan_ring(rings[0], hs, params, rng, alt_state, 0, counts)]
    for k, h in enumerate(rings[1:], start=1):
        if params['holes']:
            plans.append(plan_ring(h, hs, params, rng, alt_state, k, counts))
        else:
            plans.append([None] * len(h))

    planned = [(k, e) for k, pl in enumerate(plans) for e, p in enumerate(pl) if p]
    max_splits = params['max_splits']

    def unit_len(u):
        k, e = u['edge']
        r = rings[k]
        return math.dist(r[e], r[(e + 1) % len(r)]) * (u['t1'] - u['t0'])

    # Every round fixes at least one unit; each unit is flipped once, then
    # split or freed, and splitting stops at max_splits, so this ends
    guard = 3 * (2 ** (max_splits + 1)) * sum(len(plans[k][e]['units']) for k, e in planned) + 1
    for _ in range(guard):
        built = [build_ring(r, pl, material_left[k])
                 for k, (r, pl) in enumerate(zip(rings, plans))]
        pairs = find_crossings(built)
        for pts, tags in built:
            pairs += _repeated_points(pts, tags)

        # Fix one unit per conflict per round: changing both sides of a
        # conflict at once (e.g. at a sharp point) tends to keep them
        # clashing. Prefer the unit fixed least so far, then the shorter.
        # Conflicts between untouched pieces were already in the input
        # outline; RIGID neither causes nor fixes them.
        touched, todo = set(), []
        for a, b in pairs:
            live = [u for u in (a, b) if u is not None and not u['free']]
            if not live or any(id(u) in touched for u in live):
                continue
            pick = min(live, key=lambda u: (u['depth'], u['level'], unit_len(u)))
            touched.add(id(pick))
            todo.append(pick)
        if not todo:
            break
        for unit in todo:
            k, e = unit['edge']
            _advance(unit, plans[k][e], max_splits)
    else:
        raise ValueError("RIGID: could not resolve crossing edges")

    # Edges by final state; an edge can count in several
    fixes = {'flipped': 0, 'split': 0, 'freed': 0}
    fully_free = 0
    for k, e in planned:
        units = plans[k][e]['units']
        if any(not u['free'] and u['out'] != u['planned_out'] for u in units):
            fixes['flipped'] += 1
        if any(u['depth'] > 0 for u in units):
            fixes['split'] += 1
        if any(u['free'] for u in units):
            fixes['freed'] += 1
        if all(u['free'] for u in units):
            fully_free += 1
    rigid_edges = len(planned) - fully_free

    out_rings = [merge_collinear(pts) for pts, _ in built]
    outer, new_holes = out_rings[0], out_rings[1:]
    for k, h in enumerate(new_holes):
        if not point_in_ring(h[0], outer):
            raise ValueError(f"RIGID: hole {k + 1} ended up outside the shape")

    info = {
        'dirs': dirs,
        'tilt': tilt,
        'edges_total': sum(len(r) for r in (rings if params['holes'] else rings[:1])),
        'edges_rigid': rigid_edges,
        'edges_aligned': counts['aligned'],
        'edges_skipped': counts['skipped'],
        'vertices_before': len(rings[0]),
        'vertices_after': len(outer),
        **fixes,
    }
    return outer, new_holes, info


# ---------------------------------------------------------------------------
# Keep the result on the canvas
# ---------------------------------------------------------------------------

def fit_to_box(outer, holes, box):
    """Shift (and if needed shrink) a polygon so it lies inside box.

    Outward elbows can push the outline past the canvas edge. If the
    shape is too big for the box it is first scaled down about its own
    bounding-box centre; then it is moved just far enough to be inside.
    Shapes already inside are left alone.

    Args:
        outer: outer ring points; holes: list of hole rings
        box: (x0, y0, x1, y1) the area the shape must stay in

    Returns:
        (outer, holes, fit) - fit is None when nothing changed, else
        {'scale': s, 'dx': dx, 'dy': dy}
    """
    x0, y0, x1, y1 = box
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    if bx0 >= x0 and bx1 <= x1 and by0 >= y0 and by1 <= y1:
        return outer, holes, None

    w, h = bx1 - bx0, by1 - by0
    s = min(1.0,
            (x1 - x0) / w if w > 0 else 1.0,
            (y1 - y0) / h if h > 0 else 1.0)
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    # Bounding box after scaling about its centre
    nx0, nx1 = cx - w * s / 2, cx + w * s / 2
    ny0, ny1 = cy - h * s / 2, cy + h * s / 2
    dx = x0 - nx0 if nx0 < x0 else (x1 - nx1 if nx1 > x1 else 0.0)
    dy = y0 - ny0 if ny0 < y0 else (y1 - ny1 if ny1 > y1 else 0.0)

    def tf(ring):
        return [(cx + (x - cx) * s + dx, cy + (y - cy) * s + dy) for x, y in ring]

    return tf(outer), [tf(r) for r in holes], {'scale': s, 'dx': dx, 'dy': dy}
