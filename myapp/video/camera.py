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
        
        # Désactiver le zoom numérique si possible
        # Note: Certaines caméras ont un zoom numérique activé par défaut
        try:
            if hasattr(cv2, 'CAP_PROP_ZOOM'):
                self.cap.set(cv2.CAP_PROP_ZOOM, 0)
        except:
            pass
        
        # Désactiver l'autofocus si possible (peut causer du zoom)
        try:
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        except:
            pass
        
        w, h = resolution
        
        # Essayer de définir la résolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        # Attendre un peu pour que la caméra se stabilise
        import time
        time.sleep(0.1)
        
        # Lire quelques frames pour initialiser la caméra
        for _ in range(3):
            self.cap.read()
        
        # Vérifier la résolution réelle obtenue
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        if actual_w != w or actual_h != h:
            self.log.warning(
                "Résolution demandée %sx%s, résolution réelle %sx%s",
                w, h, actual_w, actual_h
            )
        
        self.log.info("Caméra ouverte index=%s res=%sx%s fps=%s (réel: %s)", 
                     index, actual_w, actual_h, fps, actual_fps)

    def get_frame(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def release(self):
        if self.cap:
            self.cap.release()
            self.log.info("Caméra libérée.")
