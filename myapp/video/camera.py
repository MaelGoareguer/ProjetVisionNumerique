from __future__ import annotations
import cv2, logging

class Camera:
    def __init__(self, index=0, resolution=(1280,720), fps=30):
        self.log = logging.getLogger("myapp.camera")
        self.index = index
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(index)
        if not self.cap.isOpened():
            self.log.error("Impossible d'ouvrir la caméra %s", index)
            raise RuntimeError(f"Impossible d'ouvrir la caméra {index}")
        w,h = resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.log.info("Caméra ouverte index=%s res=%sx%s fps=%s", index, w, h, fps)

    def get_frame(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        if self.cap:
            self.cap.release()
            self.log.info("Caméra libérée.")
