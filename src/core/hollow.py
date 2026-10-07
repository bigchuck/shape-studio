"""
Hollow geometry for Shape Studio - brush-stroke hollows inside a polygon

A hollow is a region cut out of a polygon, set in from its outline by a rim
of varying width, like a brush stroke following the edge. Several hollows
may sit side by side, separated by walls. Each hollow may break out to the
outside through a channel; at most one break-out per hollow keeps the
result in one piece.

Hollow regions are found in pixels (Pillow only), then turned back into
vectors:
    1. Rasterize the polygon into a mask with a small border.
    2. Depth map: repeated erosion, alternating square and cross kernels
       (an octagonal approximation of distance from the outline).
    3. Hollow = pixels deeper than a smoothly varying rim width.
    4. Walls: straight bands of varying width cut across the hollow
       region to make several hollows; connected pieces are the hollows.
    5. Trace each hollow's outline along pixel edges, simplify it to a few
       angular points, and roughen it with small angular jogs kept inside
       an allowed region (rim and walls never drop below a floor).
    6. Break-outs: a straight channel from a hollow to the outside splices
       the hollow's ring into the outer ring. The outer ring is otherwise
       kept exactly. Hollows that do not break out become holes.
"""
import math
from collections import deque

from PIL import Image, ImageDraw, ImageChops, ImageFilter

PAD = 4                         # empty border around the raster
_UNIT_LUT = [0] + [1] * 255     # 0 -> 0, anything else -> 1
_BINARY_LUT = [0] + [255] * 255


# ---------------------------------------------------------------------------
# Raster helpers
# ---------------------------------------------------------------------------

def _rasterize(points):
    """Polygon mask with a PAD border. Returns (mask, (x0, y0))."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0 = int(math.floor(min(xs))) - PAD
    y0 = int(math.floor(min(ys))) - PAD
    w = int(math.ceil(max(xs))) - x0 + PAD + 1
    h = int(math.ceil(max(ys))) - y0 + PAD + 1
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in points], fill=255)
    return mask, (x0, y0)


def _erode_cross(img):
    """Erode by a plus-shaped kernel. Relies on a zero border (offset wraps)."""
    out = img
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out = ImageChops.darker(out, ImageChops.offset(img, dx, dy))
    return out


def _dilate(img, radius):
    """Dilate a binary mask by about radius pixels."""
    if radius <= 0:
        return img
    size = 2 * int(round(radius)) + 1
    return img.filter(ImageFilter.MaxFilter(size))


def depth_map(mask, limit):
    """Approximate distance from the outside for each inside pixel.

    Repeated erosion alternating square and cross kernels gives an
    octagonal distance. Values are capped at limit.
    """
    depth = mask.point(_UNIT_LUT)
    current = mask
    for k in range(1, limit):
        if k % 2:
            current = current.filter(ImageFilter.MinFilter(3))
        else:
            current = _erode_cross(current)
        if not current.getbbox():
            break
        depth = ImageChops.add(depth, current.point(_UNIT_LUT))
    return depth


def smooth_field(size, lo, hi, wavelength, rng):
    """Smoothly varying values in [lo, hi] over an image of size."""
    w, h = size
    cells_x = max(2, int(round(w / wavelength)) + 1)
    cells_y = max(2, int(round(h / wavelength)) + 1)
    small = Image.new('L', (cells_x, cells_y))
    small.putdata([rng.randint(0, 255) for _ in range(cells_x * cells_y)])
    field = small.resize(size, Image.BICUBIC)
    lut = [int(round(lo + (hi - lo) * v / 255)) for v in range(256)]
    return field.point(lut)


# ---------------------------------------------------------------------------
# Components and tracing
# ---------------------------------------------------------------------------

def label_components(mask, min_area):
    """4-connected components of a binary mask.

    Returns:
        List of sets of (x, y) pixels, largest first, each >= min_area
    """
    w, h = mask.size
    data = bytearray(mask.tobytes())
    comps = []
    for start in range(w * h):
        if not data[start]:
            continue
        pixels = []
        queue = deque([start])
        data[start] = 0
        while queue:
            i = queue.popleft()
            x, y = i % w, i // w
            pixels.append((x, y))
            for j in ((i - 1) if x > 0 else -1, (i + 1) if x < w - 1 else -1,
                      (i - w) if y > 0 else -1, (i + w) if y < h - 1 else -1):
                if j >= 0 and data[j]:
                    data[j] = 0
                    queue.append(j)
        if len(pixels) >= min_area:
            comps.append(set(pixels))
    comps.sort(key=len, reverse=True)
    return comps


def trace_outline(pixels):
    """Outer outline of a pixel set, along pixel edges.

    Each pixel side facing outside becomes a directed unit edge, clockwise
    in screen coordinates (inside on the right). Edges are chained into
    loops, turning right first at pinch points so loops never touch
    themselves. The loop with the largest area is the outer outline; inner
    loops (islands) are dropped.

    Returns:
        List of (x, y) grid-corner points
    """
    out_edges = {}
    for x, y in pixels:
        if (x, y - 1) not in pixels:
            out_edges.setdefault((x, y), []).append((x + 1, y))
        if (x + 1, y) not in pixels:
            out_edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
        if (x, y + 1) not in pixels:
            out_edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
        if (x - 1, y) not in pixels:
            out_edges.setdefault((x, y + 1), []).append((x, y))

    loops = []
    while out_edges:
        start = next(iter(out_edges))
        loop = [start]
        cur = start
        nxt = out_edges[cur].pop()
        if not out_edges[cur]:
            del out_edges[cur]
        while True:
            d_in = (nxt[0] - cur[0], nxt[1] - cur[1])
            cur = nxt
            if cur == start and cur not in out_edges:
                break
            loop.append(cur)
            options = out_edges.get(cur)
            if not options:
                break
            if len(options) == 1:
                nxt = options.pop()
            else:
                # Prefer right turn, then straight, then left
                right = (-d_in[1], d_in[0])
                order = [right, d_in, (d_in[1], -d_in[0])]
                ranked = sorted(options, key=lambda p: order.index(
                    (p[0] - cur[0], p[1] - cur[1]))
                    if (p[0] - cur[0], p[1] - cur[1]) in order else 3)
                nxt = ranked[0]
                options.remove(nxt)
            if not options:
                del out_edges[cur]
        if len(loop) >= 4:
            loops.append(loop)

    if not loops:
        return []
    return max(loops, key=lambda l: abs(ring_area(l)))


def _dp(points, tol):
    """Douglas-Peucker on an open polyline (keeps both ends)."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        seg = math.hypot(dx, dy)
        best, best_i = -1.0, None
        for i in range(a + 1, b):
            px, py = points[i]
            if seg == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * px - dx * py + bx * ay - by * ax) / seg
            if d > best:
                best, best_i = d, i
        if best_i is not None and best > tol:
            keep[best_i] = True
            stack.append((a, best_i))
            stack.append((best_i, b))
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring, tol):
    """Douglas-Peucker on a closed ring."""
    if len(ring) < 4:
        return list(ring)
    far = max(range(len(ring)), key=lambda i: math.dist(ring[0], ring[i]))
    a = _dp(ring[:far + 1], tol)
    b = _dp(ring[far:] + [ring[0]], tol)
    return a[:-1] + b[:-1]


# ---------------------------------------------------------------------------
# Vector helpers
# ---------------------------------------------------------------------------

def ring_area(ring):
    n = len(ring)
    return sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
               for i in range(n)) / 2


def point_in_ring(pt, ring):
    x, y = pt
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def _segment_hit(p1, p2, q1, q2):
    """Proper intersection of segments p1p2 and q1q2.

    Returns:
        (t, u) parameters along each segment, or None
    """
    rx, ry = p2[0] - p1[0], p2[1] - p1[1]
    sx, sy = q2[0] - q1[0], q2[1] - q1[1]
    denom = rx * sy - ry * sx
    if abs(denom) < 1e-12:
        return None
    qpx, qpy = q1[0] - p1[0], q1[1] - p1[1]
    t = (qpx * sy - qpy * sx) / denom
    u = (qpx * ry - qpy * rx) / denom
    if 0 <= t <= 1 and 0 <= u <= 1:
        return t, u
    return None


def _segments_cross(p1, p2, q1, q2):
    """Segments intersect (including touching)."""
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)

    def on_seg(a, b, c):
        return (min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and
                min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9)

    o1, o2 = orient(p1, p2, q1), orient(p1, p2, q2)
    o3, o4 = orient(q1, q2, p1), orient(q1, q2, p2)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and on_seg(p1, p2, q1):
        return True
    if o2 == 0 and on_seg(p1, p2, q2):
        return True
    if o3 == 0 and on_seg(q1, q2, p1):
        return True
    if o4 == 0 and on_seg(q1, q2, p2):
        return True
    return False


def ring_is_simple(ring):
    """No two non-adjacent edges touch, and no repeated vertices."""
    n = len(ring)
    if n < 3 or len(set(ring)) != n:
        return False
    for i in range(n):
        a1, a2 = ring[i], ring[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _segments_cross(a1, a2, ring[j], ring[(j + 1) % n]):
                return False
    return True


def rings_disjoint(ring_a, ring_b):
    """No edge of one ring touches an edge of the other."""
    for i in range(len(ring_a)):
        a1, a2 = ring_a[i], ring_a[(i + 1) % len(ring_a)]
        for j in range(len(ring_b)):
            if _segments_cross(a1, a2, ring_b[j], ring_b[(j + 1) % len(ring_b)]):
                return False
    return True


def validate_rings(outer, holes):
    """Check an outer ring with holes is a valid hollowed polygon.

    Returns:
        None if valid, else a reason string
    """
    if not ring_is_simple(outer):
        return "outer outline intersects itself"
    for k, hole in enumerate(holes):
        if not ring_is_simple(hole):
            return f"hollow {k + 1} intersects itself"
        if not rings_disjoint(outer, hole):
            return f"hollow {k + 1} touches the outer outline"
        if not point_in_ring(hole[0], outer):
            return f"hollow {k + 1} lies outside the shape"
        for m in range(k):
            if not rings_disjoint(hole, holes[m]):
                return f"hollows {m + 1} and {k + 1} touch"
            if point_in_ring(hole[0], holes[m]) or point_in_ring(holes[m][0], hole):
                return f"hollows {m + 1} and {k + 1} overlap"
    return None


# ---------------------------------------------------------------------------
# Hollow construction
# ---------------------------------------------------------------------------

def _walls(region, count, wall_min, wall_max, rng):
    """Cut count straight walls of varying width across a hollow region.

    Walls run roughly across the region's principal axis at evenly spaced
    positions, each tilted at random and tapering from one end to the other.
    """
    if count <= 0:
        return region
    w, h = region.size
    data = region.tobytes()
    step = 3
    pts = [(x, y) for y in range(0, h, step) for x in range(0, w, step) if data[y * w + x]]
    if len(pts) < 10:
        return region
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - cx) ** 2 for p in pts)
    syy = sum((p[1] - cy) ** 2 for p in pts)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    angle = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ax, ay = math.cos(angle), math.sin(angle)
    proj = sorted((p[0] - cx) * ax + (p[1] - cy) * ay for p in pts)

    region = region.copy()
    draw = ImageDraw.Draw(region)
    for k in range(1, count + 1):
        q = k / (count + 1) + rng.uniform(-0.08, 0.08)
        q = min(max(q, 0.05), 0.95)
        s = proj[int(q * (len(proj) - 1))]
        px, py = cx + ax * s, cy + ay * s
        tilt = math.radians(rng.uniform(-25, 25))
        # Wall direction: perpendicular to the axis, tilted
        dx = -ay * math.cos(tilt) - ax * math.sin(tilt)
        dy = ax * math.cos(tilt) - ay * math.sin(tilt)
        nx, ny = -dy, dx
        # Extent of the region along the wall direction
        along = [(p[0] - px) * dx + (p[1] - py) * dy for p in pts]
        t0, t1 = min(along) - 4, max(along) + 4
        w0 = rng.uniform(wall_min, wall_max) / 2
        w1 = rng.uniform(wall_min, wall_max) / 2
        a = (px + dx * t0, py + dy * t0)
        b = (px + dx * t1, py + dy * t1)
        draw.polygon([(a[0] + nx * w0, a[1] + ny * w0), (b[0] + nx * w1, b[1] + ny * w1),
                      (b[0] - nx * w1, b[1] - ny * w1), (a[0] - nx * w0, a[1] - ny * w0)],
                     fill=0)
    return region


def _roughen(ring, allowed, spacing, amplitude, rng):
    """Add small angular jogs to a ring, staying inside allowed pixels.

    Each jog splits an edge and offsets the new point along the edge normal,
    in or out. A jog is kept only if both new edges stay in allowed pixels
    and the ring stays simple.
    """
    if amplitude <= 0 or spacing <= 0:
        return ring
    w, h = allowed.size
    data = allowed.tobytes()

    def ok(pt):
        x, y = int(round(pt[0])), int(round(pt[1]))
        return 0 <= x < w and 0 <= y < h and data[y * w + x] != 0

    def edge_ok(p, q):
        n = max(2, int(math.dist(p, q) / 2))
        return all(ok((p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n))
                   for i in range(n + 1))

    ring = list(ring)
    perimeter = sum(math.dist(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))
    jogs = int(perimeter / spacing)
    for _ in range(jogs * 3):
        if jogs <= 0:
            break
        n = len(ring)
        lengths = [math.dist(ring[i], ring[(i + 1) % n]) for i in range(n)]
        i = rng.choices(range(n), weights=lengths)[0]
        a, b = ring[i], ring[(i + 1) % n]
        if lengths[i] < 3 * amplitude:
            continue
        t = rng.uniform(0.25, 0.75)
        off = rng.uniform(amplitude / 3, amplitude) * rng.choice((-1, 1))
        ux, uy = (b[0] - a[0]) / lengths[i], (b[1] - a[1]) / lengths[i]
        p = (round(a[0] + (b[0] - a[0]) * t - uy * off),
             round(a[1] + (b[1] - a[1]) * t + ux * off))
        if p in ring or not (edge_ok(a, p) and edge_ok(p, b)):
            continue
        candidate = ring[:i + 1] + [p] + ring[i + 1:]
        if ring_is_simple(candidate):
            ring = candidate
            jogs -= 1
    return ring


def _nearest_on_ring(pt, ring):
    """Nearest point on a ring to pt. Returns (point, edge_index, t)."""
    best = None
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / l2))
        q = (a[0] + dx * t, a[1] + dy * t)
        d = math.dist(pt, q)
        if best is None or d < best[0]:
            best = (d, q, i, t)
    return best[1], best[2], best[3]


def _crossings(p, q, ring):
    """All crossings of segment pq with a ring, as (t_along_pq, ring_pos, point)."""
    hits = []
    n = len(ring)
    for i in range(n):
        hit = _segment_hit(p, q, ring[i], ring[(i + 1) % n])
        if hit:
            t, u = hit
            hits.append((t, i + u, (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)))
    return sorted(hits)


def _forward_contains(start, end, q, n):
    """Ring position q lies on the forward walk from start to end."""
    span = (end - start) % n
    return (q - start) % n <= span


def _arc(ring, start, end):
    """Ring vertices strictly between positions start and end, walking forward.

    Positions are edge_index + t along that edge.
    """
    n = len(ring)
    span = (end - start) % n
    first = math.floor(start) + 1
    out = []
    m = 0
    while first + m - start < span - 1e-9:
        out.append(ring[(first + m) % n])
        m += 1
    return out


def breakout(outer, hollow, gap_in, gap_out, rng, original, others):
    """Splice a hollow into the outer ring through a straight channel.

    A point is chosen on the hollow's edge; the channel runs from there to
    the nearest point of the original outline, gap_in wide at the hollow
    and gap_out wide at the mouth. The new outer ring walks the outer
    outline up to the channel, along one channel side into the hollow,
    around the hollow, and back out along the other side.

    Args:
        outer: Current outer ring (may already hold spliced hollows)
        hollow: Hollow ring to break out
        gap_in, gap_out: Channel width at the hollow and at the mouth
        rng: random.Random-like source
        original: The polygon's original outline - channels aim here
        others: Other hollow rings the channel must not cross

    Returns:
        New outer ring

    Raises:
        ValueError: If the channel cannot be spliced cleanly
    """
    n_h = len(hollow)
    lengths = [math.dist(hollow[i], hollow[(i + 1) % n_h]) for i in range(n_h)]
    i = rng.choices(range(n_h), weights=lengths)[0]
    t = rng.uniform(0.2, 0.8)
    a, b = hollow[i], hollow[(i + 1) % n_h]
    h = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    h_pos = i + t

    o, _, _ = _nearest_on_ring(h, original)
    _, o_edge, o_t = _nearest_on_ring(o, outer)
    o_pos = o_edge + o_t
    depth = math.dist(h, o)
    if depth < 1:
        raise ValueError("hollow touches the outline")
    ux, uy = (o[0] - h[0]) / depth, (o[1] - h[1]) / depth
    nx, ny = -uy, ux
    # Start a little inside the hollow (enough for an oblique hollow edge
    # to meet the channel sides) and end a little outside the outline
    reach_in = 1.5 * gap_in + 4
    reach_out = 0.5 * depth + 6
    start = (h[0] - ux * reach_in, h[1] - uy * reach_in)
    end = (o[0] + ux * reach_out, o[1] + uy * reach_out)

    sides = []
    for sign in (1, -1):
        p = (start[0] + sign * nx * gap_in / 2, start[1] + sign * ny * gap_in / 2)
        q = (end[0] + sign * nx * gap_out / 2, end[1] + sign * ny * gap_out / 2)
        hollow_hits = _crossings(p, q, hollow)
        if not hollow_hits:
            raise ValueError("channel side misses the hollow")
        # The crossing nearest the channel's inner end, not some far side
        # of a thin or concave hollow
        h_hit = min(hollow_hits, key=lambda c: math.dist(c[2], h))
        outer_hits = [c for c in _crossings(p, q, outer) if c[0] > h_hit[0]]
        if not outer_hits:
            raise ValueError("channel side misses the outline")
        o_hit = min(outer_hits, key=lambda c: math.dist(c[2], o))
        for other in others:
            if _crossings(h_hit[2], o_hit[2], other):
                raise ValueError("channel crosses another hollow")
        sides.append((h_hit, o_hit))

    (h1, o1), (h2, o2) = sides
    n_o = len(outer)

    # Outer part: the arc between the mouth crossings that avoids the mouth
    if _forward_contains(o1[1], o2[1], o_pos, n_o):
        outer_part = [o2[2]] + _arc(outer, o2[1], o1[1]) + [o1[2]]
    else:
        outer_part = list(reversed([o1[2]] + _arc(outer, o1[1], o2[1]) + [o2[2]]))
    # Hollow part: the arc that avoids the channel's inner end
    if _forward_contains(h1[1], h2[1], h_pos, n_h):
        hollow_part = list(reversed([h2[2]] + _arc(hollow, h2[1], h1[1]) + [h1[2]]))
    else:
        hollow_part = [h1[2]] + _arc(hollow, h1[1], h2[1]) + [h2[2]]

    ring = [(round(x), round(y)) for x, y in outer_part + hollow_part]
    # Drop consecutive duplicates introduced by rounding
    cleaned = []
    for p in ring:
        if not cleaned or cleaned[-1] != p:
            cleaned.append(p)
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
        cleaned.pop()
    if not ring_is_simple(cleaned):
        raise ValueError("break-out channel crosses the outline")
    # A splice that kept the wrong arc leaves the hollow filled - still a
    # valid ring, so check the hollow's area really left the shape
    if abs(ring_area(cleaned)) > abs(ring_area(outer)) - 0.8 * abs(ring_area(hollow)):
        raise ValueError("break-out did not open the hollow")
    return cleaned


def hollow_polygon(points, params, rng):
    """Hollow a polygon.

    Args:
        points: Outer ring of the polygon
        params: Dict with rim_min, rim_max, hollows_min, hollows_max,
                wall_min, wall_max, breakout_prob, gap_min, gap_max,
                rough, rough_spacing, simplify, wavelength
        rng: random.Random-like source

    Returns:
        (outer_ring, holes, info) - info describes what was built

    Raises:
        ValueError: If no valid hollow could be made in this attempt
    """
    points = [tuple(p) for p in points]
    rim_min, rim_max = params['rim_min'], params['rim_max']
    rough = params['rough']

    mask, (x0, y0) = _rasterize(points)
    limit = int(math.ceil(rim_max)) + 2
    depth = depth_map(mask, limit)

    # Hollow region: deeper than a smoothly varying rim width
    rim = smooth_field(mask.size, rim_min, rim_max, params['wavelength'], rng)
    region = ImageChops.subtract(depth, rim).point(_BINARY_LUT)
    if not region.getbbox():
        raise ValueError("shape is too narrow for the rim width")

    count = rng.randint(params['hollows_min'], params['hollows_max'])
    region = _walls(region, count - 1, params['wall_min'], params['wall_max'], rng)

    min_area = max(16, int((2 * rim_min) ** 2 / 4))
    comps = label_components(region, min_area)
    if not comps:
        raise ValueError("no hollow large enough")

    # Allowed area for roughening: never thinner than these floors
    rim_floor = max(2, int(rim_min * 0.5))
    wall_floor = max(2, int(params['wall_min'] * 0.5))
    deep_enough = depth.point([0 if v < rim_floor else 255 for v in range(256)])

    rings = []
    for idx, comp in enumerate(comps):
        outline = trace_outline(comp)
        ring = simplify_ring(outline, params['simplify'])
        if len(ring) < 3:
            continue
        comp_mask = Image.new('L', mask.size, 0)
        ImageDraw.Draw(comp_mask).point(list(comp), fill=255)
        others = Image.new('L', mask.size, 0)
        for jdx, other in enumerate(comps):
            if jdx != idx:
                ImageDraw.Draw(others).point(list(other), fill=255)
        allowed = ImageChops.multiply(_dilate(comp_mask, rough + 1), deep_enough)
        allowed = ImageChops.subtract(allowed, _dilate(others, wall_floor))
        ring = _roughen(ring, allowed, params['rough_spacing'], rough, rng)
        rings.append([(x + x0, y + y0) for x, y in ring])

    if not rings:
        raise ValueError("no hollow survived tracing")

    outer = list(points)
    holes = []
    broke = 0
    for k, ring in enumerate(rings):
        if rng.random() < params['breakout_prob']:
            gap_in = rng.uniform(params['gap_min'], params['gap_max'])
            gap_out = rng.uniform(params['gap_min'], params['gap_max'])
            others = rings[:k] + rings[k + 1:]
            # A poor channel point (e.g. an edge running along the channel)
            # only needs another pick, not a whole new hollow
            for attempt in range(8):
                try:
                    outer = breakout(outer, ring, gap_in, gap_out, rng, points, others)
                    break
                except ValueError:
                    if attempt == 7:
                        raise
            broke += 1
        else:
            holes.append(ring)

    reason = validate_rings(outer, holes)
    if reason:
        raise ValueError(reason)

    info = {'hollows': len(rings), 'breakouts': broke}
    return outer, holes, info
