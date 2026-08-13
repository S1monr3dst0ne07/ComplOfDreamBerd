
import sys
import time
import threading


def read():
    return sys.stdin.readline().strip('\n')

refs = {}
def follow():
    global refs

    # address to ref count
    while True:
        address = read()
        count = read()

        if not count.isdigit():
            continue

        refs[address] = int(count)


worker = threading.Thread(target=follow)
worker.start()
time.sleep(1)

for addr, count in refs.items():
    if count == 0: continue
    print(addr, count)

print("done.")




