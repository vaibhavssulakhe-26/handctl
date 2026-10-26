# handctl

Control your Linux desktop with your hand through a webcam: move the cursor, click, drag and scroll without touching anything. Built with MediaPipe, OpenCV and evdev, and it works on Wayland.

## What it does
| Gesture | Action |
|---|---|
| Move your hand | Moves the cursor (tracks the base of your index finger) |
| Pinch thumb and index finger | Click |
| Two quick pinches | Double-click |
| Pinch and hold, then move | Drag |
| Peace sign, then move your hand up or down | Scroll (joystick style: the further from the center line, the faster) |

## Requirements
- Linux with a webcam. Developed on Fedora 44 with KDE Plasma on Wayland.
- Python 3.12. MediaPipe often has no wheels for the newest Python versions.
- Permission to use `/dev/uinput`, which creates the virtual mouse.

## Setup
1. `uv python install 3.12 && uv venv --python 3.12 .venv && source .venv/bin/activate`
2. `uv pip install -r requirements.txt`
3. `./download_model.sh`
4. `sudo modprobe uinput && sudo setfacl -m u:$USER:rw /dev/uinput` (resets on reboot)
5. `QT_QPA_PLATFORM=xcb python hand_mouse.py`

Press `q` in the camera window to quit. It also stops by itself after a few minutes as a safety limit.

## Tuning
The settings are constants at the top of `hand_mouse.py`:
- `X_MIN, X_MAX, Y_MIN, Y_MAX`: the part of the camera view that maps to the whole screen. A smaller box means less hand travel.
- `PINCH_ON, PINCH_OFF`: how close the fingers must be to press and to release.
- `MIN_CUTOFF, BETA`: smoothing. Lower `MIN_CUTOFF` is steadier, higher `BETA` has less lag.
- `CLICK_FREEZE, DRAG_HOLD`: timing for double-clicks and drags.
- `SCROLL_DEADZONE, SCROLL_GAIN, SCROLL_DIR`: scroll feel and direction.
- `RUN_SECONDS`: the safety time limit.

## How it works
MediaPipe finds 21 hand landmarks per frame. A One Euro filter smooths the cursor position, a thumb-to-index distance divided by hand size detects pinches, and a virtual mouse created through `/dev/uinput` injects the events.

## Scripts
`scripts/` has small tests for each stage: `cam_test.py` (webcam), `hand_test.py` (landmarks), `pinch_test.py` (live pinch ratio) and `vmouse_test.py` (the virtual mouse moves in a circle).

## Known limits
- One hand at a time, and it needs decent lighting.
- Linux only.
- Landmarks get less reliable near the edges of the camera view.

## License
MIT. See [LICENSE](LICENSE).
