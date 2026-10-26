from evdev import UInput, AbsInfo, ecodes as e

MAX = 32767

class VirtualMouse:
    def __init__(self):
        cap = {
            e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
            e.EV_ABS: [
                (e.ABS_X, AbsInfo(value=0, min=0, max=MAX, fuzz=0, flat=0, resolution=0)),
                (e.ABS_Y, AbsInfo(value=0, min=0, max=MAX, fuzz=0, flat=0, resolution=0)),
            ],
        }
        self.ui = UInput(cap, name="handctl-mouse")
        wheel_cap = {
            e.EV_KEY: [e.BTN_LEFT],
            e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL, e.REL_WHEEL_HI_RES],
        }
        self.wheel = UInput(wheel_cap, name="handctl-wheel")

    def move(self, nx, ny):
        nx = min(max(nx, 0.0), 1.0)
        ny = min(max(ny, 0.0), 1.0)
        self.ui.write(e.EV_ABS, e.ABS_X, int(nx * MAX))
        self.ui.write(e.EV_ABS, e.ABS_Y, int(ny * MAX))
        self.ui.syn()

    def button(self, down):
        self.ui.write(e.EV_KEY, e.BTN_LEFT, 1 if down else 0)
        self.ui.syn()

    def scroll(self, notches):
        if notches == 0:
            return
        self.wheel.write(e.EV_REL, e.REL_WHEEL_HI_RES, notches * 120)
        self.wheel.write(e.EV_REL, e.REL_WHEEL, notches)
        self.wheel.syn()

    def close(self):
        self.ui.close()
        self.wheel.close()
