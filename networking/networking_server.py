import socket
import math
import json


class NetworkingServer:

    def send(self, conn, global_pos):
        print(f"[Server] global: ({global_pos[0]:.2f}, {global_pos[1]:.2f})", flush=True)
        msg = json.dumps({"global": global_pos}) + "\n"
        conn.sendall(msg.encode("utf-8"))

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 0.0.0.0 = accept connections from other computers, not just this one
        sock.bind(("0.0.0.0", 8001))
        sock.listen()
        print("Waiting for a client to connect...", flush=True)

        conn, address = sock.accept()
        reader = conn.makefile("r", encoding="utf-8")
        print("Client connected", flush=True)

        while True:
            line = reader.readline()
            if not line:
                break

            d = json.loads(line)
            global_pos = self.transform_local_to_global(
                d["camera_pos"], d["camera_res"], d["bounding_box"], d["HFOV"], d["VFOV"])
            self.send(conn, global_pos)

        conn.close()
        sock.close()
        print("Conversation finished.")

    def transform_local_to_global(self, camera_pos, camera_res, bounding_box, HFOV, VFOV):
        camera_angle = math.radians(45)
        drone_rotation = math.radians(45)
        drone_mid_dist = camera_pos['z'] * math.tan(camera_angle)
        middle_pos = {'x': camera_pos['x'] + drone_mid_dist * math.sin(drone_rotation), 'y': camera_pos['y'] + drone_mid_dist * math.cos(drone_rotation)}

        x_prime = 2 * camera_pos['z'] * math.tan(math.radians(HFOV / 2))
        y_prime = 2 * camera_pos['z'] * math.tan(math.radians(VFOV / 2))

        local_pos = {'x_min': bounding_box['x_min'] / camera_res['x'],
                     'y_min': bounding_box['y_min'] / camera_res['y'],
                     'x_max': bounding_box['x_max'] / camera_res['x'],
                     'y_max': bounding_box['y_max'] / camera_res['y']}

        mine_x_local = (local_pos['x_min'] + local_pos['x_max']) / 2
        mine_y_local = (local_pos['y_min'] + local_pos['y_max']) / 2

        x_local_dist = mine_x_local - 0.5
        y_local_dist = mine_y_local - 0.5

        x_global_dist = x_local_dist * x_prime
        y_global_dist = y_local_dist * y_prime

        mine_global_x = middle_pos['x'] + x_global_dist
        mine_global_y = middle_pos['y'] - y_global_dist

        return (mine_global_x, mine_global_y)


if __name__ == "__main__":
    server = NetworkingServer()
    server.run()
