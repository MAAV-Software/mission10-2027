import math
import numpy

camera_pos = {'x': 0, 'y': 3.0338, 'z': 2}
camera_resolution = {'x': 3280, 'y': 2464}

HFOV = 62.2
VFOV = 48.8

x_prime = 2 * camera_pos['z'] * math.tan(math.radians(HFOV / 2))
y_prime = 2 * camera_pos['z'] * math.tan(math.radians(VFOV / 2))

bounding_box = {'x_min': 2301.284912109375, 'y_min': 1487.0400390625, 
                'x_max': 2487.232666015625, 'y_max': 1679.614013671875}

local_pos = {'x_min': bounding_box['x_min'] / camera_resolution['x'], 
             'y_min': bounding_box['y_min'] / camera_resolution['y'], 
             'x_max': bounding_box['x_max'] / camera_resolution['x'], 
             'y_max': bounding_box['y_max'] / camera_resolution['y']}

mine_x_local = (local_pos['x_min'] + local_pos['x_max']) / 2
mine_y_local = (local_pos['y_min'] + local_pos['y_max']) / 2

x_local_dist = mine_x_local - 0.5
y_local_dist = mine_y_local - 0.5

x_global_dist = x_local_dist * x_prime
y_global_dist = y_local_dist * y_prime

print(x_global_dist)
mine_global_x = camera_pos['x'] + x_global_dist

mine_global_y = camera_pos['y'] - y_global_dist

print(f'mine_global_x: {mine_global_x}, mine_global_y: {mine_global_y}')
