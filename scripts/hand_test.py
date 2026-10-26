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

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
start = time.time()

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    timestamp_ms = int((time.time() - start) * 1000)
    result = detector.detect_for_video(mp_image, timestamp_ms)

    h, w = frame.shape[:2]
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        for lm in hand:
            cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (0, 255, 0), -1)
        tip = hand[8]  # index fingertip
        cv2.circle(frame, (int(tip.x * w), int(tip.y * h)), 10, (0, 0, 255), -1)

    cv2.imshow("hand", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
