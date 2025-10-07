from __future__ import annotations
import logging
from typing import Any

class VideoProcessor:
    """
    Base pour tous les modules de traitement.
    Un module doit implémenter process_frame(frame) -> frame (np.ndarray BGR ou GRAY).
    """
    def __init__(self, name: str | None = None, config: dict | None = None, **kwargs: Any):
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.kwargs = kwargs
        self.log = logging.getLogger(f"myapp.proc.{self.name}")

    def process_frame(self, frame):
        raise NotImplementedError("Implémentez process_frame(frame)")

    def close(self):
        pass
