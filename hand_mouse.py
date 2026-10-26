import math
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from vmouse import VirtualMouse

RUN_SECONDS = 180          # auto-quit failsafe
X_MIN, X_MAX = 0.25, 0.75
Y_MIN, Y_MAX = 0.25, 0.65
PINCH_ON, PINCH_OFF = 0.25, 0.35
CLICK_FREEZE = 0.3         # cursor stays frozen this long after a click
DRAG_HOLD = 0.4            # hold pinch longer than this to drag
MOVE_EPS = 0.001           # don't send moves smaller than this

# One Euro filter: lower MIN_CUTOFF = steadier when still,
# higher BETA = less lag when moving fast
MIN_CUTOFF = 0.8
BETA = 6.0

# Joystick scroll
SCROLL_DEADZONE = 0.04     # hand offset (fraction of frame) with no scrolling
SCROLL_GAIN = 40           # notches/sec per unit of offset past the deadzone
SCROLL_DIR = 1             # 1 = hand above center scrolls up; -1 flips it


class OneEuro:
    def __init__(self, min_cutoff, beta, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.reset()

    def reset(self):
        self.x = None
        self.dx = 0.0
        self.t = None

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        if self.x is None:
            self.x, self.t = x, t
            return x
        dt = max(t - self.t, 1e-3)
        a_d = self._alpha(self.d_cutoff, dt)
        self.dx = a_d * ((x - self.x) / dt) + (1 - a_d) * self.dx
        cutoff = self.min_cutoff + self.beta * abs(self.dx)
        a = self._alpha(cutoff, dt)
        self.x = a * x + (1 - a) * self.x
        self.t = t
        return self.x


options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.6,
)
detector = vision.HandLandmarker.create_from_options(options)


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def remap(v, lo, hi):
    return min(max((v - lo) / (hi - lo), 0.0), 1.0)


def extended(hand, tip, pip):
    return hand[tip].y < hand[pip].y


mouse = VirtualMouse()
fx_filter = OneEuro(MIN_CUTOFF, BETA)
fy_filter = OneEuro(MIN_CUTOFF, BETA)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

start = time.time()
sx, sy = 0.5, 0.5            # last position sent to the mouse
pinching = False
pinch_start = 0.0
release_time = 0.0
below = 0
scroll_frames = 0
scroll_anchor = None
scroll_acc = 0.0
last_t = time.time()
fps = 0.0

try:
    while time.time() - start < RUN_SECONDS:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        now = time.time()
        dt = max(now - last_t, 1e-3)
        result = detector.detect_for_video(mp_image, int((now - start) * 1000))

        h, w = frame.shape[:2]
        mode = ""
        if result.hand_landmarks:
            hand = result.hand_landmarks[0]
            p = hand[5]
            tx = remap(p.x, X_MIN, X_MAX)
            ty = remap(p.y, Y_MIN, Y_MAX)
            fx = fx_filter(tx, now)
            fy = fy_filter(ty, now)
            ratio = dist(hand[4], hand[8]) / dist(hand[0], hand[9])

            is_scroll = (extended(hand, 8, 6) and extended(hand, 12, 10)
                         and not extended(hand, 16, 14) and not extended(hand, 20, 18))
            scroll_frames = scroll_frames + 1 if is_scroll else 0
            scrolling = scroll_frames >= 3

            if scrolling:
                mode = "SCROLL"
                if pinching:
                    pinching = False
                    release_time = now
                    mouse.button(False)
                y = hand[9].y
                if scroll_anchor is None:
                    scroll_anchor = y
                offset = y - scroll_anchor
                if abs(offset) > SCROLL_DEADZONE:
                    sign = 1 if offset > 0 else -1
                    speed = (abs(offset) - SCROLL_DEADZONE) * SCROLL_GAIN
                    scroll_acc += -sign * speed * dt * SCROLL_DIR
                    n = int(scroll_acc)
                    if n:
                        mouse.scroll(n)
                        scroll_acc -= n
                cy = int(scroll_anchor * h)
                cv2.line(frame, (0, cy), (w, cy), (0, 255, 255), 2)
            else:
                scroll_anchor = None
                scroll_acc = 0.0

                if not pinching:
                    below = below + 1 if ratio < PINCH_ON else 0
                    if below >= 2:
                        pinching = True
                        pinch_start = now
                        below = 0
                        mouse.button(True)
                elif ratio > PINCH_OFF:
                    pinching = False
                    release_time = now
                    mouse.button(False)

                can_move = ((pinching and now - pinch_start > DRAG_HOLD)
                            or (not pinching and now - release_time > CLICK_FREEZE))
                if can_move and math.hypot(fx - sx, fy - sy) > MOVE_EPS:
                    sx, sy = fx, fy
                    mouse.move(sx, sy)
                if pinching:
                    mode = "PINCH"

            cv2.circle(frame, (int(p.x * w), int(p.y * h)), 8,
                       (0, 0, 255) if pinching else (0, 255, 0), -1)
        else:
            fx_filter.reset()
            fy_filter.reset()
            scroll_frames = 0
            scroll_anchor = None
            below = 0
            if pinching:
                pinching = False
                release_time = now
                mouse.button(False)

        fps = 0.9 * fps + 0.1 * (1.0 / dt)
        last_t = now
        cv2.rectangle(frame, (int(X_MIN * w), int(Y_MIN * h)),
                      (int(X_MAX * w), int(Y_MAX * h)), (255, 255, 0), 2)
        cv2.putText(frame, f"FPS {fps:.0f}  {mode}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("hand mouse", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    mouse.button(False)
    mouse.close()
    cap.release()
    cv2.destroyAllWindows()
