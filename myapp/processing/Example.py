from __future__ import annotations
from myapp.processing.base import VideoProcessor

class HandExample(VideoProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = None 

    def process_frame(self, frame):
        return frame
