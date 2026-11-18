import socket
import json

class NetworkingServer:

    def __init__(self, insults):
        self.insults = insults

    def send(self, conn, message):
        print(f"[Person 2]: {message}", flush=True)
        msg = json.dumps({"message": message}) + "\n"
        conn.sendall(msg.encode("utf-8"))

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 8000))
        sock.listen()
        print("Waiting for a client to connect...", flush=True)

        conn, address = sock.accept()
        reader = conn.makefile("r", encoding="utf-8")
        print("Client connected", flush=True)

        while True:
            line = reader.readline()
            if not line:
                break

            insult = json.loads(line)["message"]

            index = self.insults.index(insult)
            if index + 1 >= len(self.insults):
                break

            self.send(conn, self.insults[index + 1])

            if index + 1 == len(self.insults) - 1:
                break

        conn.close()
        sock.close()
        print("Conversation finished.")


if __name__ == "__main__":
    from networking_client import INSULTS

    server = NetworkingServer(INSULTS)
    server.run()
