from __future__ import annotations
from myapp.processing.base import VideoProcessor

class HandYolo(VideoProcessor):
    """
    Détection/pose des mains via Ultralytics YOLO.
    kwargs (depuis engines.yolo) : weights, task, conf, iou, classes, imgsz, device, draw_scores, draw_pose
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from myapp.engines.yolo_engine import YoloEngine
        self.draw_scores = bool(self.kwargs.pop("draw_scores", True))
        self.draw_pose = bool(self.kwargs.pop("draw_pose", True))
        self.engine = YoloEngine(**self.kwargs)

    def process_frame(self, frame):
        results = self.engine.infer(frame)
        return self.engine.draw(frame, results, draw_scores=self.draw_scores, draw_pose=self.draw_pose)

    def close(self):
        if self.engine:
            self.engine.close()
