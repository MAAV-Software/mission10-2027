"""Convert YOLO bounding boxes (image pixels) to global ground coordinates.

World frame: X = east/right, Y = north/forward, Z = up, ground plane at Z = 0.
Drone yaw is measured clockwise from +Y (compass style), so yaw = 0 looks
along +Y and yaw = 90 deg looks along +X.
Camera tilt is measured from straight down: 0 = nadir, 45 deg = halfway to
the horizon. The top of the image points in the yaw direction.

Each bounding-box center is cast as a ray through a pinhole camera model and
intersected with the ground plane.
"""

import math

import numpy as np

# ---------------- Config ----------------
camera_pos = {'x': 0, 'y': 3.0338, 'z': 2}      # z = height above ground
camera_resolution = {'x': 3280, 'y': 2464}
camera_angle = math.radians(45)                  # tilt from straight down
drone_rotation = math.radians(45)                # yaw, clockwise from +Y

HFOV = math.radians(62.2)
VFOV = math.radians(48.8)


def camera_basis(tilt, yaw):
    """Return the camera's (right, down, forward) unit vectors in world frame."""
    heading = np.array([math.sin(yaw), math.cos(yaw), 0.0])   # horizontal forward
    right = np.array([math.cos(yaw), -math.sin(yaw), 0.0])
    up = np.array([0.0, 0.0, 1.0])

    forward = math.sin(tilt) * heading - math.cos(tilt) * up   # optical axis
    image_up = math.cos(tilt) * heading + math.sin(tilt) * up  # top of image
    return right, -image_up, forward


def pixel_to_global(u, v, cam_pos=camera_pos, tilt=camera_angle,
                    yaw=drone_rotation, resolution=camera_resolution,
                    hfov=HFOV, vfov=VFOV):
    """Project pixel (u, v) onto the ground plane.

    u is the column (0 = left), v is the row (0 = top), in pixels.
    Returns (x, y) in world coordinates, or None if the pixel's ray
    doesn't hit the ground (at or above the horizon).
    """
    w, h = resolution['x'], resolution['y']
    fx = (w / 2) / math.tan(hfov / 2)    # focal lengths in pixels
    fy = (h / 2) / math.tan(vfov / 2)

    # Ray direction in camera frame (x right, y down, z forward)
    x_c = (u - w / 2) / fx
    y_c = (v - h / 2) / fy

    right, down, forward = camera_basis(tilt, yaw)
    ray = x_c * right + y_c * down + forward

    if ray[2] >= 0:                      # pointing at or above the horizon
        return None

    origin = np.array([cam_pos['x'], cam_pos['y'], cam_pos['z']])
    t = -origin[2] / ray[2]              # distance along ray to reach Z = 0
    hit = origin + t * ray
    return float(hit[0]), float(hit[1])


def bbox_to_global(bbox, **kwargs):
    """Global (x, y) of a bounding box's center. bbox is in pixels."""
    u = (bbox['x_min'] + bbox['x_max']) / 2
    v = (bbox['y_min'] + bbox['y_max']) / 2
    return pixel_to_global(u, v, **kwargs)


if __name__ == "__main__":
    bounding_box = {'x_min': 2301.284912109375, 'y_min': 1487.0400390625,
                    'x_max': 2487.232666015625, 'y_max': 1679.614013671875}

    result = bbox_to_global(bounding_box)
    if result is None:
        print("Mine is above the horizon; can't project to ground")
    else:
        mine_global_x, mine_global_y = result
        print(f'mine_global_x: {mine_global_x}, mine_global_y: {mine_global_y}')
