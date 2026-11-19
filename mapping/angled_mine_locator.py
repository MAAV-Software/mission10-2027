"""
mine_locator.py - find where a mine is on the field from where it appears in a drone photo.

How it works (per detected mine):
  1. photo position (u, v)  -> the direction the camera was looking   (camera frame)
  2. rotate that direction by the camera's tilt / heading           (world frame)
  3. follow that ray down until it hits the ground                  (ray-plane intersection)
  4. optional: redo step 3 with the real terrain height until it settles (bumpy ground)

Conventions (same as Blender):
  world   x = east, y = north, z = up, meters
  image   u = right, v = down, both 0-1, (0, 0) = top-left corner  (YOLO convention)
  camera  rotation is Blender's XYZ Euler, in degrees
            rot_x = tilt     0 = straight down, 45 = looking 45 deg ahead, 90 = at the horizon
            rot_y = keep 0 for a normal drone gimbal
            rot_z = heading  0 = top of the photo faces +y (north), positive = counter-clockwise
          A compass heading (clockwise from north) converts as rot_z = -compass_deg.
"""

import math
from dataclasses import dataclass


# ----------------------------------------------------------------------------- vector helpers

def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _rotation_xyz(rx, ry, rz):
    """3x3 rotation matrix for Blender XYZ Euler angles (radians): R = Rz @ Ry @ Rx."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return (
        (cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx),
        (sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx),
        (-sy,     cy * sx,                cy * cx),
    )


def _column(m, i):
    return (m[0][i], m[1][i], m[2][i])


# ----------------------------------------------------------------------------- camera

@dataclass
class Camera:
    x: float              # camera position on the field (meters)
    y: float
    z: float              # camera altitude, world z (meters) - NOT height above ground
    rot_x: float = 0.0    # tilt (degrees)
    rot_y: float = 0.0
    rot_z: float = 0.0    # heading (degrees)
    hfov: float = 62.2    # horizontal field of view (degrees), Pi Camera v2
    vfov: float = 48.8    # vertical field of view (degrees), Pi Camera v2

    @property
    def position(self):
        return (self.x, self.y, self.z)

    def axes(self):
        """The camera's right, down and forward directions, as world-space unit vectors."""
        r = _rotation_xyz(math.radians(self.rot_x), math.radians(self.rot_y), math.radians(self.rot_z))
        right = _column(r, 0)
        up = _column(r, 1)
        back = _column(r, 2)          # a Blender camera looks down its own -Z axis
        return right, _scale(up, -1), _scale(back, -1)


# ----------------------------------------------------------------------------- core math

def pixel_to_ray(cam, u, v):
    """Step 1 + 2: photo position (u, v) -> direction in world space (not normalized)."""
    xn = (2 * u - 1) * math.tan(math.radians(cam.hfov) / 2)   # sideways, per unit forward
    yn = (2 * v - 1) * math.tan(math.radians(cam.vfov) / 2)   # downward, per unit forward
    right, down, forward = cam.axes()
    return _add(_add(_scale(right, xn), _scale(down, yn)), forward)


def pixel_to_ground(cam, u, v, ground_z=0.0, terrain=None, max_iters=20, tol=1e-4):
    """
    Step 3 (+4): where the pixel's ray hits the ground.

    ground_z  height of the ground in world z, used when the ground is treated as flat
    terrain   optional function terrain(x, y) -> ground z, for bumpy ground. The ray is
              re-intersected at the terrain height of the previous guess until it settles.

    Returns (x, y, z) in meters, or None if the ray points at or above the horizon.
    """
    d = pixel_to_ray(cam, u, v)
    if d[2] >= 0:
        return None                               # never comes back down to the ground

    z = terrain(cam.x, cam.y) if terrain else ground_z
    for _ in range(max_iters):
        t = (z - cam.z) / d[2]                    # how far along the ray to drop to height z
        p = _add(cam.position, _scale(d, t))
        if terrain is None:
            return p
        new_z = terrain(p[0], p[1])
        if new_z is None:
            return None                           # ray landed outside the terrain
        if abs(new_z - z) < tol:
            return (p[0], p[1], new_z)
        z = new_z
    return p                                      # very steep terrain: return best guess


def ground_to_pixel(cam, x, y, z=0.0):
    """Inverse: world point -> (u, v) in the photo. Returns None if it's behind the camera."""
    right, down, forward = cam.axes()
    rel = (x - cam.x, y - cam.y, z - cam.z)
    depth = _dot(rel, forward)
    if depth <= 0:
        return None
    xn = _dot(rel, right) / depth
    yn = _dot(rel, down) / depth
    u = (xn / math.tan(math.radians(cam.hfov) / 2) + 1) / 2
    v = (yn / math.tan(math.radians(cam.vfov) / 2) + 1) / 2
    return u, v


# ----------------------------------------------------------------------------- YOLO labels

def read_yolo(path):
    """Read a YOLO label file -> list of (class_id, x_center, y_center, width, height)."""
    boxes = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 5:
                c, xc, yc, w, h = parts[:5]
                boxes.append((int(c), float(xc), float(yc), float(w), float(h)))
    return boxes


def locate_boxes(boxes, cam, ground_z=0.0, terrain=None, point="center"):
    """
    Turn YOLO boxes into field coordinates.

    point  "center" - use the box center (best for flat objects like mines)
           "bottom" - use the bottom-middle of the box (where tall objects touch the ground)
    """
    results = []
    for c, xc, yc, w, h in boxes:
        u, v = (xc, yc + h / 2) if point == "bottom" else (xc, yc)
        p = pixel_to_ground(cam, u, v, ground_z=ground_z, terrain=terrain)
        results.append({"class": c, "u": u, "v": v,
                        "x": None if p is None else p[0],
                        "y": None if p is None else p[1],
                        "z": None if p is None else p[2]})
    return results


def locate_file(label_path, cam, ground_z=0.0, terrain=None, point="center"):
    """Read a YOLO label file and return the field coordinates of every box in it."""
    return locate_boxes(read_yolo(label_path), cam, ground_z, terrain, point)


# ----------------------------------------------------------------------------- self-test

def _self_test():
    import random

    # 1. worked example: 3.16 m up, tilted 45 deg, facing north, mine at (0.6, 0.3) in the photo
    cam = Camera(0, 0, 3.16, rot_x=45)
    x, y, _ = pixel_to_ground(cam, 0.6, 0.3)
    assert abs(x - 0.659) < 1e-3 and abs(y - 4.561) < 1e-3, (x, y)

    # 2. straight down must match the whiteboard formula: x = cam_x + (u - 0.5) * 2h*tan(hfov/2)
    cam = Camera(1.0, -2.0, 3.16)
    x, y, _ = pixel_to_ground(cam, 0.25, 0.8)
    width = 2 * 3.16 * math.tan(math.radians(62.2) / 2)
    length = 2 * 3.16 * math.tan(math.radians(48.8) / 2)
    assert abs(x - (1.0 + (0.25 - 0.5) * width)) < 1e-9
    assert abs(y - (-2.0 - (0.8 - 0.5) * length)) < 1e-9

    # 3. round trip: random poses and pixels -> ground -> pixel must come back unchanged
    rng = random.Random(0)
    worst = 0.0
    for _ in range(5000):
        cam = Camera(rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(2, 20),
                     rot_x=rng.uniform(0, 60), rot_z=rng.uniform(-180, 180))
        u, v = rng.random(), rng.random()
        p = pixel_to_ground(cam, u, v)
        if p is None:
            continue
        uu, vv = ground_to_pixel(cam, *p)
        worst = max(worst, abs(uu - u), abs(vv - v))
    assert worst < 1e-9, worst

    # 4. bumpy terrain: a point on a hill must be found on the hill, not on flat ground
    def hill(x, y):
        return 0.4 * math.sin(x) * math.cos(y)
    cam = Camera(0, 0, 3.4, rot_x=40, rot_z=30)
    target = (0.8, 2.5, hill(0.8, 2.5))
    u, v = ground_to_pixel(cam, *target)
    p = pixel_to_ground(cam, u, v, terrain=hill)
    assert math.dist(p, target) < 1e-3, (p, target)

    print("all self-tests passed (worst round-trip error %.1e)" % worst)


# ----------------------------------------------------------------------------- command line

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Locate mines on the field from a YOLO label file.")
    ap.add_argument("labels", nargs="?", help="YOLO .txt label file (omit to run self-tests)")
    ap.add_argument("--cam", nargs=3, type=float, metavar=("X", "Y", "Z"), help="camera position (m)")
    ap.add_argument("--tilt", type=float, default=0.0, help="tilt in degrees (0 = straight down)")
    ap.add_argument("--heading", type=float, default=0.0, help="Blender rot_z in degrees")
    ap.add_argument("--ground", type=float, default=0.0, help="ground height in world z (m)")
    ap.add_argument("--hfov", type=float, default=62.2)
    ap.add_argument("--vfov", type=float, default=48.8)
    args = ap.parse_args()

    if not args.labels:
        _self_test()
    else:
        if not args.cam:
            ap.error("--cam X Y Z is required with a label file")
        cam = Camera(*args.cam, rot_x=args.tilt, rot_z=args.heading, hfov=args.hfov, vfov=args.vfov)
        for r in locate_file(args.labels, cam, ground_z=args.ground):
            if r["x"] is None:
                print(f"class {r['class']}: box at ({r['u']:.3f}, {r['v']:.3f}) is above the horizon")
            else:
                print(f"class {r['class']}: box at ({r['u']:.3f}, {r['v']:.3f}) -> "
                      f"field ({r['x']:.3f}, {r['y']:.3f}) m")