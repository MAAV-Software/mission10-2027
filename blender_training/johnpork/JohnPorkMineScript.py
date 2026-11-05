import bpy
import math
import os

x = 0
y = 0
z = 0

cam = bpy.context.scene.camera

cam.rotation_euler.x = 0
cam.rotation_euler.y = 0
cam.rotation_euler.z = 0

cam.location.x = 0.5
cam.location.y = 0.5
cam.location.z = 1.05

h_fov = 62.2
v_fov = 48.8

dir = "C:/Users/Pengu/OneDrive/Desktop/mine_pics/labels"

bpy.context.scene.render.engine = "CYCLES"

bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
bpy.context.scene.cycles.device = "GPU"

bpy.context.scene.cycles.samples = 1
bpy.context.scene.cycles.use_denoising = False

scene = bpy.context.scene

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 3280
scene.render.resolution_y = 2464
scene.render.resolution_percentage = 100

#get localized xy coords
def find_localized_coord(fovType):
    return 2 * (cam.location.z) * math.tan(math.radians(fovType)/2)

localized_x = find_localized_coord(h_fov)
localized_y = find_localized_coord(v_fov)

#get relative mine YOLO coords
mine_x_coords = [0.201459, 0.740416, 0.635376, 0.349]
mine_y_coords = [0.37215, 0.637673, 0.179254, 0.662]

mine_x_size = 0.0715
mine_y_size = 0.0415
mine_rotations = [90, -47.668, -45.594, 0]

iterations = 12
for n in range(iterations):
    x = 0
    cam.location.x, cam.location.y = x, y
    
    for j in range(iterations):
        cam.location.x, cam.location.y = x, y
        label_path = os.path.join(dir, f"grass{9 + (n * iterations + j)}.txt")
        for i in range(len(mine_x_coords)):
            #center of the mines
            x_dist = (mine_x_coords[i] - cam.location.x) / localized_x
            y_dist = (mine_y_coords[i] - cam.location.y) / localized_y
            print("X DIST: " + str(x_dist))
            print("Y DIST: " + str(y_dist))
            print("CAMERA X: " + str(cam.location.x))

            relative_x = 0.5 + x_dist
            relative_y = (0.5 - y_dist)
            
            #sizes of the mines
            x_len = (mine_x_size * abs(math.cos(math.radians(mine_rotations[i])))) + (mine_y_size * abs(math.sin(math.radians(mine_rotations[i]))))
            y_len = (mine_y_size * abs(math.sin(math.radians(mine_rotations[i]) + (0.5 * math.pi)))) + (mine_x_size * abs(math.cos(math.radians(mine_rotations[i]) + (0.5 * math.pi))))

            localized_len_x = x_len / localized_x
            localized_len_y = y_len / localized_y

            if(0 <= relative_x <= 1 and 0 <= relative_y <= 1):
                metadata = f"0 {relative_x} {relative_y} {localized_len_x} {localized_len_y}"
                with open(label_path, "a") as f:
                    f.write(metadata + ("\n" if metadata else ""))

            cam.keyframe_insert(data_path="location", frame=1)
                    
        img_file = "C:/Users/Pengu/OneDrive/Desktop/mine_pics/images/grass" + str(9 + (n * iterations + j)) + ".png"
        scene.frame_set(1)
        scene.render.filepath = img_file
        bpy.ops.render.render(write_still=True)
        x += 1/iterations
    y += 1/iterations




#iterations = 10
#n = 0

#for i in range(iterations):
#    for i in range(iterations):
#        n += 1
#        cam.location.x, cam.location.y = x, y

#        cam.keyframe_insert(data_path="location", frame=1)
#        
#        img_file = "C:/Users/Pengu/img" + str(n) + ".png"
#        scene.frame_set(1)
#        scene.render.filepath = img_file
#        bpy.ops.render.render(write_still=True)
#        x -= iterations/10
#    x = 0.5
#    y -= iterations/10
#    
    

    