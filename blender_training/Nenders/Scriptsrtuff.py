import bpy
import os
from math import tan, radians

scene = bpy.context.scene
cam = scene.camera

# Save mine locations
objs = bpy.data.objects

mine_0_x = objs["IARC_PFM-1_mine"].matrix_world.translation.x
mine_0_y = objs["IARC_PFM-1_mine"].matrix_world.translation.y

mine_1_x = objs["IARC_PFM-1_mine.001"].matrix_world.translation.x
mine_1_y = objs["IARC_PFM-1_mine.001"].matrix_world.translation.y

mine_2_x = objs["IARC_PFM-1_mine.002"].matrix_world.translation.x
mine_2_y = objs["IARC_PFM-1_mine.002"].matrix_world.translation.y

mine_3_x = objs["IARC_PFM-1_mine.003"].matrix_world.translation.x
mine_3_y = objs["IARC_PFM-1_mine.003"].matrix_world.translation.y

mine_4_x = objs["IARC_PFM-1_mine.004"].matrix_world.translation.x
mine_4_y = objs["IARC_PFM-1_mine.004"].matrix_world.translation.y

mine_5_x = objs["IARC_PFM-1_mine.005"].matrix_world.translation.x
mine_5_y = objs["IARC_PFM-1_mine.005"].matrix_world.translation.y

mines = [
    (mine_0_x, mine_0_y),
    (mine_1_x, mine_1_y),
    (mine_2_x, mine_2_y),
    (mine_3_x, mine_3_y),
    (mine_4_x, mine_4_y),
    (mine_5_x, mine_5_y),
]


# Save location
out_dir = r"C:\Users\noahe\Desktop\UM School files\MAAV\YoloRenders"
images_dir = os.path.join(out_dir, "images")
labels_dir = os.path.join(out_dir, "labels")
os.makedirs(images_dir, exist_ok=True)
os.makedirs(labels_dir, exist_ok=True)
name = "frame_test14_"

# Plane dimensions
xPlaneLen = 2
yPlaneLen = 2

# Camera view dimensions on the ground (based on z)
cam.location.z = 1.2

xprime = 2 * cam.location.z * tan(radians(62.2 / 2))
yprime = 2 * cam.location.z * tan(radians(48.8 / 2))

# Clac starting coords (top left)
cam.location.x = -(xPlaneLen/2) + xprime / 2
cam.location.y =  (yPlaneLen/2) - yprime / 2

# Camera partitions:
xPartitionsCount = 5
yPartitionsCount = 5
dx = (xPlaneLen - xprime) / (xPartitionsCount - 1)
dy = (yPlaneLen - yprime) / (yPartitionsCount - 1)

start_x = cam.location.x
start_y = cam.location.y

mine_width = 0.12 / xprime
mine_height = 0.12 / yprime

# Render settings (Courtosy of Claude)
scene.render.engine = "CYCLES"
bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
scene.cycles.device = "GPU"
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.cycles.tile_size = 512

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 3280
scene.render.resolution_y = 2464
scene.render.resolution_percentage = 100

img = 0
for i in range(xPartitionsCount):
    cam.location.x = start_x + i * dx

    for j in range(yPartitionsCount):
        cam.location.y = start_y - j * dy

        # Write YOLO labels for mines in the camera's field of view
        with open(os.path.join(labels_dir, f"{name}{img:04d}.txt"), "w") as f:
            for mine_x, mine_y in mines:
                if (abs(mine_x - cam.location.x) <= xprime / 2 and
                        abs(mine_y - cam.location.y) <= yprime / 2):
                    x_center = (mine_x - cam.location.x) / xprime + 0.5
                    y_center = 0.5 - (mine_y - cam.location.y) / yprime
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {mine_width:.6f} {mine_height:.6f}\n")

        scene.render.filepath = os.path.join(images_dir, f"{name}{img:04d}.png")
        bpy.ops.render.render(write_still=True)
        img += 1