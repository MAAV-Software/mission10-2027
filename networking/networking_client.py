import socket
import json


class NetworkingClient:

    def __init__(self, coordinates):
        self.coordinates = coordinates

    def send(self, sock, detection):
        box = detection["bounding_box"]
        cam = detection["camera_pos"]
        print(f"[Client] local:  box ({box['x_min']}, {box['y_min']}) -> ({box['x_max']}, {box['y_max']}) "
              f"from camera at ({cam['x']}, {cam['y']}, {cam['z']})", flush=True)
        msg = json.dumps(detection) + "\n"
        sock.sendall(msg.encode("utf-8"))

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 8000))
        reader = sock.makefile("r", encoding="utf-8")

        for detection in self.coordinates:
            self.send(sock, detection)
            line = reader.readline()
            if not line:
                break

        sock.close()
        print("Conversation finished.")


CAMERA_RES = {"x": 1920, "y": 1080}
HFOV = 69
VFOV = 42

TEST_COOR = [
    {"camera_pos": {"x": 0, "y": 0, "z": 10},
     "bounding_box": {"x_min": 940, "y_min": 520, "x_max": 980, "y_max": 560}},
    {"camera_pos": {"x": 0, "y": 0, "z": 10},
     "bounding_box": {"x_min": 100, "y_min": 100, "x_max": 160, "y_max": 160}},
    {"camera_pos": {"x": 5, "y": 2, "z": 8},
     "bounding_box": {"x_min": 1500, "y_min": 800, "x_max": 1560, "y_max": 860}},
    {"camera_pos": {"x": -3, "y": 4, "z": 12},
     "bounding_box": {"x_min": 300, "y_min": 900, "x_max": 340, "y_max": 940}},
]

for detection in TEST_COOR:
    detection.update({"camera_res": CAMERA_RES, "HFOV": HFOV, "VFOV": VFOV})


if __name__ == "__main__":
    client = NetworkingClient(TEST_COOR)
    client.run()
