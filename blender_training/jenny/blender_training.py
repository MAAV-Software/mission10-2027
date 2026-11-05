import bpy
import math
import random
import os

def move_camera(camz):

    cam = bpy.context.scene.camera
    cam.location.x = 0.3
    cam.location.y = 0.55
    cam.location.z = camz
    for j in range(3):
        if j % 2 == 0:
            for i in range(11):
                render_image(i + 11 * j)
                if i != 10:
                    cam.location.y -= 0.1
        else:
            for i in range(11):
                render_image(i + 11 * j)
                if i != 10:
                    cam.location.y += 0.1
        if j != 2:
            cam.location.x -= 0.3

def render_image(index):
    
    cam = bpy.context.scene.camera
    mines = [
        obj for obj in bpy.data.objects
        if obj.name.startswith("IARC_PFM-1_mine")
        and obj.type == "MESH"
    ]
            
    hfov = cam.data.angle_x
    vfov = cam.data.angle_y

    # cam.rotation_euler.z = rand_rotation

    cam.keyframe_insert(data_path="location", frame=1)

    bpy.context.scene.render.engine = "CYCLES"

    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    bpy.context.scene.cycles.device = "GPU"

    bpy.context.scene.cycles.samples = 1
    bpy.context.scene.cycles.use_denoising = False

    scene = bpy.context.scene

    scene.render.image_settings.file_format = 'JPEG'
    scene.render.resolution_x = 3280
    scene.render.resolution_y = 2464
    scene.render.resolution_percentage = 100

    img_file = fr"E:\UMSI\MAAV\blender_training\img\{index}.jpg"
    scene.frame_set(1)
    scene.render.filepath = img_file
    bpy.ops.render.render(write_still=True)

    label_file = fr"E:\UMSI\MAAV\blender_training\label\{index}.txt"
    
    with open(label_file, "w") as f:
        
        for mine in mines:
            
            h = cam.location.z - mine.location.z
            x_length = 2 * h * math.tan(hfov/2)
            y_length = 2 * h * math.tan(vfov/2)
            x_center = 0.5 - (cam.location.x - mine.location.x)/x_length
            y_center = 0.5 + (cam.location.y - mine.location.y)/y_length
            width = mine.dimensions.x / x_length
            height = mine.dimensions.y / y_length
    
            xmin = x_center - width / 2
            xmax = x_center + width / 2
            ymin = y_center - height / 2
            ymax = y_center + height / 2
    
            if xmax > 0 and xmin < 1 and ymax > 0 and ymin < 1:
                xmin = max(0.0, xmin)
                xmax = min(1.0, xmax)
                ymin = max(0.0, ymin)
                ymax = min(1.0, ymax)
        
                x_center = (xmin + xmax) / 2
                y_center = (ymin + ymax) / 2
                width = xmax - xmin
                height = ymax - ymin        
                f.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
def main():
    os.makedirs(r"E:\UMSI\MAAV\blender_training\img", exist_ok=True)
    os.makedirs(r"E:\UMSI\MAAV\blender_training\label", exist_ok=True)

    move_camera(0.5)
    return 0

if __name__ == "__main__":
    main()