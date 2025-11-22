from __future__ import annotations

class YoloEngine:
    """
    Wrapper Ultralytics YOLO pour la détection/pose de mains.
    - task: "detect" (boîtes) | "pose" (keypoints) selon les poids fournis
    - weights: chemin .pt
    """
    def __init__(
        self,
        *,
        weights: str,
        task: str = "detect",
        conf: float = 0.25,
        iou: float = 0.45,
        classes: list[int] | None = None,
        imgsz: int | tuple[int, int] = 640,
        half: bool = False,
        device: str | None = None,
        **kwargs
    ):
        try:
            from ultralytics import YOLO  
        except ImportError as e:
            # Vérifier si c'est un problème avec ultralytics ou ses dépendances
            error_msg = str(e).lower()
            if "pillow" in error_msg or "pil" in error_msg:
                raise ImportError(
                    "Le moteur YOLO nécessite 'Pillow' (PIL). Réinstallez-le:\n"
                    "pip uninstall Pillow pillow -y && pip install Pillow"
                ) from e
            else:
                raise ImportError(
                    "Le moteur YOLO nécessite 'ultralytics' et ses dépendances.\n"
                    "Installez-les avec: pip install ultralytics\n"
                    f"Erreur originale: {e}"
                ) from e
        except Exception as e:
            raise ImportError(
                f"Erreur lors de l'import d'ultralytics: {e}\n"
                "Assurez-vous que ultralytics est correctement installé:\n"
                "pip install --upgrade ultralytics"
            ) from e

        self.YOLO = YOLO
        self.model = YOLO(weights)
        self.task = task
        self.conf = float(conf)
        self.iou = float(iou)
        self.classes = classes
        self.imgsz = imgsz
        self.half = half
        self.device = device

    def infer(self, frame_bgr):
        results = self.model(
            source=frame_bgr,
            conf=self.conf,
            iou=self.iou,
            classes=self.classes,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False
        )
        return results[0]

    def draw(self, frame_bgr, results, draw_scores: bool = True, draw_pose: bool = True):
        import cv2
        if results is None:
            return frame_bgr

        # POSE
        if self.task == "pose" and getattr(results, "keypoints", None) is not None:
            annotated = results.plot()
            return annotated

        # DETECT
        if getattr(results, "boxes", None) is not None and results.boxes is not None:
            boxes = results.boxes
            for b in boxes:
                xyxy = b.xyxy[0].tolist()
                conf = float(b.conf[0]) if b.conf is not None else None
                cls_id = int(b.cls[0]) if b.cls is not None else -1
                x1, y1, x2, y2 = map(int, xyxy)
                cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                if draw_scores and conf is not None:
                    label = f"hand {conf:.2f}" if cls_id in (-1, 0, 1) else f"id{cls_id} {conf:.2f}"
                    cv2.putText(frame_bgr, label, (x1, max(0, y1 - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
        return frame_bgr

    def close(self):
        pass
