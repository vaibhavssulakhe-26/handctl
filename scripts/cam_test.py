import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Cannot open webcam")

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)  # mirror, so your hand moves the way you expect
    cv2.imshow("cam", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
