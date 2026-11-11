import math
import random

import bpy
import bpy_extras
from mathutils import Vector

# max camera move
x_i = -0.286945
y_i = 0.329822
x_f = 0.255673
y_f = -0.318045

N_FRAMES = 100
SCENE_EVERY = 10           # re-randomize the scene (frame-driven seed/HDRI/grass) every N shots; other shots only move the camera
Z_MIN, Z_MAX = 0.25, 1.2   # camera height range; tune so mines span ~3%-30% of image width
TILT_STD_DEG = 3.0         # small random tilt, real shots are never perfectly top-down
BACKGROUND_EVERY = 5       # every Nth frame hides the mines -> empty label (hard negative)
MIN_BOX_PX = 10            # drop boxes smaller than this (width or height, in pixels)
MIN_INFRAME_FRAC = 0.4     # drop mines with less than this fraction of their box inside the frame
MIN_VISIBLE_FRAC = 0.3     # drop mines where fewer than this fraction of sample rays reach them
RAY_SAMPLES = 9            # rays per mine for the occlusion check
MAX_POSE_TRIES = 200       # re-pick camera pose until the frame shows only ground
SEED = 0
FILE_PREFIX = "data_"

scene = bpy.context.scene
cam = scene.camera

SPAWNER_OBJ_NAME = "mineSpawner"  # the Empty with the GN modifier
ID_ATTR = "mine_id"               # name used in the Store Named Attribute node

# Render setup
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 1      
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_x = 3280
scene.render.resolution_y = 2464
#scene.render.resolution_x = 1312
#scene.render.resolution_y = 986
scene.render.resolution_percentage = 100

img_path = "/Users/somebody4545/Documents/maav/data/images/"
data_path = "/Users/somebody4545/Documents/maav/data/labels/"

spawner = bpy.data.objects[SPAWNER_OBJ_NAME]

scene.render.use_persistent_data = True  # keep scene loaded to improve render speed


def get_mine_point_groups(depsgraph):
    """Return {mine_id: [world-space Vector, ...]} from the spawner's realized output."""
    groups = {}
    found_mesh = False

    for inst in depsgraph.object_instances:
        if not inst.is_instance or inst.parent is None:
            continue
        if inst.parent.original.name != SPAWNER_OBJ_NAME:
            continue
        if inst.object.type != "MESH":
            continue

        mesh = inst.object.data
        found_mesh = True

        attr = mesh.attributes.get(ID_ATTR)
        if attr is None:
            raise RuntimeError(
                f"Attribute '{ID_ATTR}' not found on spawner output. "
                f"Available: {[a.name for a in mesh.attributes]}"
            )
        if attr.domain != "POINT":
            raise RuntimeError(f"'{ID_ATTR}' is on domain {attr.domain}, expected POINT")

        n = len(mesh.vertices)
        ids = [0] * n
        attr.data.foreach_get("value", ids)
        coords = [0.0] * (n * 3)
        mesh.vertices.foreach_get("co", coords)

        mw = inst.matrix_world.copy()
        for k in range(n):
            p = mw @ Vector((coords[3 * k], coords[3 * k + 1], coords[3 * k + 2]))
            groups.setdefault(ids[k], []).append(p)

    if not found_mesh:
        raise RuntimeError(f"No mesh output found from '{SPAWNER_OBJ_NAME}'")
    return groups


def visible_fraction(depsgraph, points_world):
    origin = cam.matrix_world.translation
    center = sum(points_world, Vector()) / len(points_world)
    radius = max((p - center).length for p in points_world)
    tol = radius * 1.1 + 1e-4

    targets = [center] + random.sample(points_world, min(RAY_SAMPLES - 1, len(points_world)))
    reached = 0
    for t in targets:
        direction = t - origin
        dist = direction.length
        hit, loc, *_ = scene.ray_cast(depsgraph, origin, direction.normalized(), distance=dist + tol)
        if not hit or (loc - center).length <= tol:
            reached += 1
    return reached / len(targets)


def compute_yolo_box(points_world):
    projected = [bpy_extras.object_utils.world_to_camera_view(scene, cam, p) for p in points_world]

    if any(v.z <= 0 for v in projected):
        return None

    xs = [v.x for v in projected]
    ys = [1.0 - v.y for v in projected]  # YOLO origin is top-left

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    if max_x < 0.0 or min_x > 1.0 or max_y < 0.0 or min_y > 1.0:
        return None

    full_area = (max_x - min_x) * (max_y - min_y)

    min_x, max_x = max(0.0, min_x), min(1.0, max_x)
    min_y, max_y = max(0.0, min_y), min(1.0, max_y)

    width = max_x - min_x
    height = max_y - min_y

    #ignore if not visible enough
    if full_area <= 0 or width * height / full_area < MIN_INFRAME_FRAC:
        return None 
    if width * scene.render.resolution_x < MIN_BOX_PX or height * scene.render.resolution_y < MIN_BOX_PX:
        return None

    return (min_x + width / 2.0, min_y + height / 2.0, width, height)


random.seed(SEED)

cam.animation_data_clear()

try:
    for frame in range(N_FRAMES):
        if frame % SCENE_EVERY == 0:
            scene.frame_set(frame // SCENE_EVERY)

        background = BACKGROUND_EVERY > 0 and frame % BACKGROUND_EVERY == BACKGROUND_EVERY - 1
        spawner.hide_render = background
        spawner.hide_viewport = background

        cam.location = (
            random.uniform(x_i, x_f),
            random.uniform(y_f, y_i),
            random.uniform(Z_MIN, Z_MAX),
        )
        cam.rotation_euler = (
            math.radians(random.gauss(0, TILT_STD_DEG)),
            math.radians(random.gauss(0, TILT_STD_DEG)),
            random.uniform(0, 2 * math.pi),  # yaw
        )
        bpy.context.view_layer.update()

        name = f"{FILE_PREFIX}{frame:04d}"
        scene.render.filepath = f"{img_path}{name}"
        bpy.ops.render.render(write_still=True)

        written = 0
        n_mines = 0
        with open(f"{data_path}{name}.txt", "w", encoding="utf-8") as file:
            if not background:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                groups = get_mine_point_groups(depsgraph)
                n_mines = len(groups)
                for mine_id, pts in groups.items():
                    box = compute_yolo_box(pts)
                    if box is None:
                        continue
                    if visible_fraction(depsgraph, pts) < MIN_VISIBLE_FRAC:
                        continue
                    cx, cy, w, h = box
                    file.write(f"0 {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
                    written += 1

        kind = "background" if background else f"{n_mines} mines in scene, {written} labeled"
        print(f"{name}: z={cam.location.z:.2f}, {kind}")
finally:
    spawner.hide_render = False
    spawner.hide_viewport = False
