import time
from multiprocessing import Process
from pathfinding.pathfinding import a_star
from pathfinding.pathfinding import render
from itertools import count

from networking.networking_client import NetworkingClient, TEST_COOR
from networking.networking_server import NetworkingServer


def run_server():
    NetworkingServer().run()


def run_client():
    NetworkingClient(TEST_COOR).run()

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