import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modules.camera_module import CameraModule

cfg = {
    "camera_type": "usb",
    "camera_id": 0,
    "width": 1280,
    "height": 720,
    "fps": 30
}

cam = CameraModule("test_cam", cfg)
ok = cam.initialize()
print("initialize() ->", ok)
if ok:
    info = cam.get_info()
    print("info:", info)
    cam.cleanup()
