import bpy
import math
import random
import os

scene = bpy.context.scene
cam = scene.camera

output_dir = "/Users/joelzoto/Documents/MAAV/Training Data"
os.makedirs(output_dir, exist_ok=True)

mine_x, mine_y, mine_z = 4.1072, 1.2298, 5.9047
mine_width = 2.14    # size along world X
mine_length = 1.18   # size along world Y

HFOV = 62.2
VFOV = 48.8

cam.rotation_euler = (0, 0, 0)
cam.data.sensor_fit = 'HORIZONTAL'
cam.data.angle_x = math.radians(HFOV)
cam.location = (1.04, -3.5, 30)


scene.render.engine = "CYCLES"
bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"
scene.cycles.device = "GPU"
scene.cycles.samples = 1
scene.cycles.use_denoising = False

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 3280
scene.render.resolution_y = 2464
scene.render.resolution_percentage = 100

for i in range(10):

    scene.render.filepath = os.path.join(output_dir, f"render{i}.png")
    bpy.ops.render.render(write_still=True)

   
    dist = cam.location.z - mine_z
    x_prime = 2 * dist * math.tan(math.radians(HFOV / 2))
    y_prime = 2 * dist * math.tan(math.radians(VFOV / 2))

    x_center = 0.5 + (mine_x - cam.location.x) / x_prime
    y_center = 0.5 - (mine_y - cam.location.y) / y_prime
    w = mine_width / x_prime
    h = mine_length / y_prime

 
    x_min = max(0.0, x_center - w / 2)
    x_max = min(1.0, x_center + w / 2)
    y_min = max(0.0, y_center - h / 2)
    y_max = min(1.0, y_center + h / 2)

    label_path = os.path.join(output_dir, f"render{i}.txt")
    if x_max > x_min and y_max > y_min:
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        cw = x_max - x_min
        ch = y_max - y_min
        metadata = f"0 {cx:.6f} {cy:.6f} {cw:.6f} {ch:.6f}"
    else:
        metadata = ""  
        
    with open(label_path, "w") as f:
        f.write(metadata + ("\n" if metadata else ""))

    cam.location.y += 1.5
    if cam.location.x < 2:
        cam.location.x += random.randint(2, 6)
    else:
        cam.location.x -= random.randint(2, 6)