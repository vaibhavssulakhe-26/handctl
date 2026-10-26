import math
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

options = vision.HandLandmarkerOptions(
    base_options=mp_python.BaseOptions(model_asset_path="hand_landmarker.task"),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
)
detector = vision.HandLandmarker.create_from_options(options)

def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
start = time.time()
PINCH_THRESHOLD = 0.25

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect_for_video(mp_image, int((time.time() - start) * 1000))

    h, w = frame.shape[:2]
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        thumb, index = hand[4], hand[8]
        hand_size = dist(hand[0], hand[9])
        ratio = dist(thumb, index) / hand_size
        pinching = ratio < PINCH_THRESHOLD

        color = (0, 0, 255) if pinching else (0, 255, 0)
        cv2.line(frame, (int(thumb.x * w), int(thumb.y * h)),
                 (int(index.x * w), int(index.y * h)), color, 3)
        cv2.putText(frame, f"ratio {ratio:.2f}  x {index.x:.2f}  y {index.y:.2f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if pinching:
            cv2.putText(frame, "PINCH", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("pinch", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
