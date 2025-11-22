from __future__ import annotations
import cv2
import logging
from pathlib import Path
from typing import Optional

class VideoPlayer:
    """
    Lecteur vidéo avec contrôles gestuels.
    """
    def __init__(self, video_path: str | Path):
        self.log = logging.getLogger("myapp.video_player")
        self.video_path = Path(video_path)
        
        if not self.video_path.exists():
            raise FileNotFoundError(f"Fichier vidéo non trouvé: {video_path}")
        
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la vidéo: {video_path}")
        
        # Propriétés de la vidéo
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # État de lecture
        self.is_playing = False
        self.current_frame = 0
        
        # Vitesse de défilement (frames à sauter pour avancer/reculer)
        self.skip_frames = int(self.fps * 2)  # 2 secondes par geste
        
        self.log.info(
            "Vidéo chargée: %s (%sx%s, %s fps, %s frames)",
            self.video_path.name, self.width, self.height, self.fps, self.total_frames
        )
    
    def get_frame(self) -> Optional[tuple]:
        """
        Lit la frame actuelle.
        Retourne (frame, frame_number, total_frames) ou None si fin de vidéo.
        """
        if self.current_frame >= self.total_frames:
            return None
        
        # Positionner la vidéo sur la frame actuelle
        target_frame = int(self.current_frame)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
        # Lire la frame actuelle
        ret, frame = self.cap.read()
        
        if not ret or frame is None:
            # Si la lecture échoue, essayer de réinitialiser et relire
            self.log.debug(f"Tentative de repositionnement pour la frame {target_frame}")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            # Lire jusqu'à la frame cible
            for i in range(min(target_frame + 1, self.total_frames)):
                ret, frame = self.cap.read()
                if not ret:
                    self.log.warning(f"Impossible de lire la frame {i} lors du repositionnement")
                    return None
                if i == target_frame:
                    break
        
        if frame is None or frame.size == 0:
            self.log.warning(f"Frame {self.current_frame} est vide ou invalide")
            return None
        
        return (frame, self.current_frame, self.total_frames)
    
    def play(self):
        """Démarre la lecture."""
        self.is_playing = True
        self.log.debug("Lecture démarrée")
    
    def pause(self):
        """Met en pause."""
        self.is_playing = False
        self.log.debug("Pause activée")
    
    def toggle_play_pause(self):
        """Bascule entre play et pause."""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def advance(self):
        """Avance dans la vidéo."""
        new_frame = min(self.current_frame + self.skip_frames, self.total_frames - 1)
        self.current_frame = new_frame
        self.log.debug(f"Avance: frame {self.current_frame}/{self.total_frames}")
    
    def rewind(self):
        """Recule dans la vidéo."""
        new_frame = max(self.current_frame - self.skip_frames, 0)
        self.current_frame = new_frame
        self.log.debug(f"Recule: frame {self.current_frame}/{self.total_frames}")
    
    def update(self):
        """
        Met à jour la position de lecture si en mode play.
        Retourne True si la vidéo continue, False si fin de vidéo.
        """
        if self.is_playing:
            self.current_frame += 1
            if self.current_frame >= self.total_frames:
                self.pause()
                self.current_frame = self.total_frames - 1
                return False
        return True
    
    def set_position(self, frame_number: int):
        """Définit la position de lecture."""
        self.current_frame = max(0, min(frame_number, self.total_frames - 1))
    
    def get_position(self) -> float:
        """Retourne la position actuelle en secondes."""
        return self.current_frame / self.fps if self.fps > 0 else 0
    
    def get_duration(self) -> float:
        """Retourne la durée totale en secondes."""
        return self.total_frames / self.fps if self.fps > 0 else 0
    
    def release(self):
        """Libère les ressources."""
        if self.cap:
            self.cap.release()
            self.log.info("Vidéo libérée")

