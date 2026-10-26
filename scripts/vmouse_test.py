import math
import time
from vmouse import VirtualMouse

m = VirtualMouse()
time.sleep(1)  # give KWin a moment to notice the new device

start = time.time()
while time.time() - start < 5:
    t = time.time() - start
    m.move(0.5 + 0.2 * math.cos(t * 2), 0.5 + 0.2 * math.sin(t * 2))
    time.sleep(0.01)

m.close()
