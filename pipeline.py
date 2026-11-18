import time
from multiprocessing import Process
from pathfinding.pathfinding import a_star
from pathfinding.pathfinding import render
import heapq
from itertools import count

from networking.networking_client import NetworkingClient
from networking.networking_server import NetworkingServer

INSULTS = ["Watch it jerk", "Shut up idiot",
           "Moron", "Scab eater",
           "Butt sniffer", "pus licker",
           "Fart smeller", "You eat dog crap for breakfast",
           "Geek", "You mixed your weeds with your mama’s toe jam",
           "You bob for apples in the toilet and you like it", "You play ball like a girl",
           "What did you say to me?", "You heard what i said",
           "Tomorrow, noon, here at our field, get the buffalo butt breather",
           "Count on it pee crap drinking face"]





def run_server():
    NetworkingServer(INSULTS).run()


def run_client():
    NetworkingClient(INSULTS).run()

if __name__ == "__main__":
    server = Process(target=run_server)
    server.start()

    time.sleep(0.5)

    client = Process(target=run_client)
    client.start()

    client.join()
    server.join()

    W, H = 10, 6
    MINES = {(3, 0), (3, 1), (3, 2), (3, 3), (6, 2), (6, 3), (6, 4), (6, 5)}
    p = a_star(W, H, MINES, (0, 0), (9, 5))
    print(render(W, H, MINES, p))
    print(f"\nLength: {len(p) - 1} steps" if p else "\nNo path")