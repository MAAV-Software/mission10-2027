import math


def mine_position(u, v, cam_x, cam_y, height, tilt, heading, hfov=62.2, vfov=48.8):
    t = math.radians(tilt)
    h = math.radians(heading)

    # 1. photo position -> direction, as offsets per 1 unit along the lens
    right = (2 * u - 1) * math.tan(math.radians(hfov) / 2)    # + = right of center
    down = (2 * v - 1) * math.tan(math.radians(vfov) / 2)     # + = below center

    # 2. tilt: how far that direction goes forward and down for each step along it
    forward_per_step = math.sin(t) - down * math.cos(t)
    drop_per_step = math.cos(t) + down * math.sin(t)
    if drop_per_step <= 0:
        return None                                   # points at or above the horizon

    # 3. follow it down until it has dropped the full height
    steps = height / drop_per_step
    dx = right * steps                                # meters to the camera's right
    dy = forward_per_step * steps                     # meters ahead of the camera

    # 4. turn by the heading, then add the drone's position
    x = cam_x + dx * math.cos(h) - dy * math.sin(h)
    y = cam_y + dx * math.sin(h) + dy * math.cos(h)
    return x, y


if __name__ == "__main__":
    # example: drone at (0, 0), 3.16 m above the grass, tilted 45 deg, facing north,
    # mine box centered at (0.6, 0.3) in the photo  ->  about (0.66, 4.56)
    print(mine_position(0.6, 0.3, 0, 0, 3.16, 45, 0))
