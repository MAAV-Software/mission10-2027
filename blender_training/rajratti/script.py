import bpy
import cv2
import math
import random
import os
import re

HFOV = math.radians(62.2)
VFOV = math.radians(48.8)

CAM_HEIGHT = 1
CLASS_ID = 0
GRID = 10
MIN_VISIBLE_FRACTION = 0.3 

corners = [(-2.1255, 1.9863, 0.15781), (1.5499, 2.0364, -0.19135), 
           (-2.0623, -1.9942, -0.028407), (1.3821, -2.0153, 0.13126)]

field_length = max(corners[0][1], corners[1][1]) - min(corners[2][1], corners[3][1])
field_width = max(corners[1][0], corners[3][0]) - min(corners[0][0], corners[2][0])

mine_width = 0.171
mine_length = 0.0942

train_val_split = 0.8
SPLIT_SEED = 0         # Fixed seed

image_train_folder = "/Users/rajratti/maav-workspace/YOLO/dataset/images/train/"
image_val_folder = "/Users/rajratti/maav-workspace/YOLO/dataset/images/val/"
label_train_folder = "/Users/rajratti/maav-workspace/YOLO/dataset/labels/train/"
label_val_folder = "/Users/rajratti/maav-workspace/YOLO/dataset/labels/val/"
video_folder = "/Users/rajratti/maav-workspace/YOLO/"

video_name = "output_video.mp4"
for folder in (image_train_folder, image_val_folder,
               label_train_folder, label_val_folder, video_folder):
    os.makedirs(folder, exist_ok=True)

# Train/val split
num_images = (5) * (5) + GRID * GRID
num_val = round(num_images * (1 - train_val_split))
random.seed(SPLIT_SEED)
val_indices = set(random.sample(range(num_images), num_val))

# Camera setup
scene = bpy.context.scene
cam = scene.camera

cam.rotation_euler = (0, 0, 0)          # face straight down
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.angle_x = HFOV

scene.render.engine = "CYCLES"
bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"
scene.cycles.device = "GPU"
scene.cycles.samples = 1
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 3280
scene.render.resolution_y = 2464
scene.render.resolution_percentage = 100

# Add the mines, coordinates, and 
mine_names = []
MINES_NUM = 16

for i in range(MINES_NUM):
    if (i <= 9):    
        mine_names.append(f"IARC_PFM-1_mine.00{i}")
    elif (i >= 10):
        mine_names.append(f"IARC_PFM-1_mine.0{i}")

mines = []
for name in mine_names:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object not found: {name}")
    pos = obj.matrix_world.to_translation()
    yaw = obj.matrix_world.to_euler().z
    # Footprint of the rotated mine, as an axis-aligned box in world X/Y
    footprint_x = abs(mine_width * math.cos(yaw)) + abs(mine_length * math.sin(yaw))
    footprint_y = abs(mine_width * math.sin(yaw)) + abs(mine_length * math.cos(yaw))
    mines.append((pos.x, pos.y, pos.z, footprint_x, footprint_y))


def yolo_line(mine, cam_x, cam_y, cam_z):
    """YOLO label line for one mine, or '' if it isn't (enough) in frame."""
    mx, my, mz, fx, fy = mine

    d = cam_z - mz                              # depth from camera to mine
    if d <= 0:
        return ""

    img_w = 2 * d * math.tan(HFOV / 2)          # ground width seen at mine depth
    img_h = 2 * d * math.tan(VFOV / 2)          # ground height seen at mine depth

    u = 0.5 + (mx - cam_x) / img_w              # 0 = left edge, 1 = right edge
    v = 0.5 - (my - cam_y) / img_h              # 0 = top edge, 1 = bottom (YOLO)
    w = fx / img_w
    h = fy / img_h

    # Box edges, then clip to the image
    x0, x1 = u - w / 2, u + w / 2
    y0, y1 = v - h / 2, v + h / 2
    cx0, cx1 = max(0.0, x0), min(1.0, x1)
    cy0, cy1 = max(0.0, y0), min(1.0, y1)

    if cx1 <= cx0 or cy1 <= cy0:                # completely outside (checks BOTH axes)
        return ""
    if (cx1 - cx0) * (cy1 - cy0) < MIN_VISIBLE_FRACTION * w * h:
        return ""                               # only a sliver is visible

    return (f"{CLASS_ID} {(cx0 + cx1) / 2:.6f} {(cy0 + cy1) / 2:.6f} "
            f"{cx1 - cx0:.6f} {cy1 - cy0:.6f}\n")


# ---------------- Render loop ----------------
rendered_images = []   # every image path in grid order, for the video

#for i in range(GRID):
#    for j in range(GRID):
#        n = GRID * i + j

#        # Choose train or val folders for this shot
#        if n in val_indices:
#            image_folder, label_folder = image_val_folder, label_val_folder
#        else:
#            image_folder, label_folder = image_train_folder, label_train_folder

#        # Divide by (GRID - 1) so the grid reaches both edges of the field
#        cam.location = (
#            min(corners[0][0], corners[2][0]) + (field_width / (GRID - 1)) * i,
#            min(corners[2][1], corners[3][1]) + (field_length / (GRID - 1)) * j,
#            CAM_HEIGHT,
#        )
#        cam.keyframe_insert(data_path="location", frame=10)
#        scene.frame_set(10)

#        # Label file has the same name as the image -> YOLO pairs them
#        txt_file = os.path.join(label_folder, f"test_pic_{n}.txt")
#        with open(txt_file, "w", encoding="utf-8") as f:
#            for mine in mines:
#                f.write(yolo_line(mine, cam.location.x, cam.location.y, cam.location.z))

#        image_path = os.path.join(image_folder, f"test_pic_{n}.png")
#        scene.render.filepath = image_path
#        bpy.ops.render.render(write_still=True)
#        rendered_images.append(image_path)

CAM_HEIGHT = 2

for i in range(5):
    for j in range(5):
        n = (5) * i + j
        
        if n in val_indices:
            image_folder, label_folder = image_val_folder, label_val_folder
        else:
            image_folder, label_folder = image_train_folder, label_train_folder

        # Divide by (GRID - 1) so the grid reaches both edges of the field
        cam.location = (
            min(corners[0][0], corners[2][0]) + (field_width / (GRID/2 - 1)) * i,
            min(corners[2][1], corners[3][1]) + (field_length / (GRID/2 - 1)) * j,
            CAM_HEIGHT,
        )
        cam.keyframe_insert(data_path="location", frame=10)
        scene.frame_set(10)

        # Label file has the same name as the image -> YOLO pairs them
        txt_file = os.path.join(label_folder, f"test_pic_{100+n}.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            for mine in mines:
                f.write(yolo_line(mine, cam.location.x, cam.location.y, cam.location.z))

        image_path = os.path.join(image_folder, f"test_pic_{100+n}.png")
        scene.render.filepath = image_path
        bpy.ops.render.render(write_still=True)
        rendered_images.append(image_path)
            

print(f"Done: {num_images - num_val} train, {num_val} val")


# ---------------- Video ----------------
# Uses images from both train and val, in the order they were shot
first = cv2.imread(rendered_images[0])
height, width, _ = first.shape

fps = 24.0
duration_per_image = 0.2
frames_per_image = int(fps * duration_per_image)

video = cv2.VideoWriter(os.path.join(video_folder, video_name),
                        cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

for image_path in rendered_images:
    frame = cv2.imread(image_path)
    for _ in range(frames_per_image):
        video.write(frame)

video.release()