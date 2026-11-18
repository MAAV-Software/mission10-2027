import socket
import json


class NetworkingClient:

    def __init__(self, insults):
        self.insults = insults

    def send(self, sock, message):
        print(f"[Person 1]: {message}", flush=True)
        msg = json.dumps({"message": message}) + "\n"
        sock.sendall(msg.encode("utf-8"))

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 8000))
        reader = sock.makefile("r", encoding="utf-8")

        self.send(sock, self.insults[0])

        while True:
            line = reader.readline()
            if not line:
                break

            reply = json.loads(line)["message"]

            index = self.insults.index(reply)
            if index + 1 >= len(self.insults):
                break

            insult = self.insults[index + 1]
            self.send(sock, insult)

            if insult == self.insults[-1]:
                break

        sock.close()
        print("Conversation finished.")


INSULTS = ["Watch it jerk", "Shut up idiot",
           "Moron", "Scab eater",
           "Butt sniffer", "pus licker",
           "Fart smeller", "You eat dog crap for breakfast",
           "Geek", "You mixed your weeds with your mama’s toe jam",
           "You bob for apples in the toilet and you like it", "You play ball like a girl",
           "What did you say to me?", "You heard what i said",
           "Tomorrow, noon, here at our field, get the buffalo butt breather",
           "Count on it pee crap drinking face"]


if __name__ == "__main__":
    client = NetworkingClient(INSULTS)
    client.run()