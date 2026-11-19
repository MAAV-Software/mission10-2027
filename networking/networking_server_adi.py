import socket
import json 

class NetworkingServer:

    def send(self, conn, payload):
        print(f"[Server] sending: {payload}", flush=True)
        msg = json.dumps(payload) + "\n"
        conn.sendall(msg.encode("utf-8"))

    def handle(self, request):
        cam_x, cam_y, cam_z = request["camera"]
        box = compute_yolo(request["mine"], cam_x, cam_y, cam_z)

        if box is None:
            return {"visible": False, "label": "", "box": None}

        label = (f"{box['class_id']} {box['x_center']:.6f} {box['y_center']:.6f} "
                f"{box['width']:.6f} {box['height']:.6f}")
        return {"visible": True, "label": label, "box": box}

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen()
        print("Waiting for a client to connect...", flush=True)

        conn, address = sock.accept()
        reader = conn.makefile("r", encoding="utf-8")
        print("Client connected", flush=True)

        while True:
            line = reader.readline()
            if not line:                # client disconnected
                break

            request = json.loads(line)
            print(f"[Server] received: {request}", flush=True)
            self.send(conn, self.handle(request))

        reader.close()
        conn.close()
        sock.close()
        print("Conversation finished.")

if __name__ == "__main__":
    NetworkingServer().run()