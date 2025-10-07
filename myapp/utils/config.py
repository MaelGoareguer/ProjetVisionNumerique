from __future__ import annotations
from pathlib import Path
import yaml, logging

_DEFAULTS = {
    "camera": {"index": 0, "resolution": [1280,720], "fps": 30},
    "engines": {"yolo": {}},
    "logging": {
        "level": "INFO",
        "handlers": {"console": True, "file": "log/app.log"},
        "format": "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
    },
}

def load_settings(candidates):
    log = logging.getLogger("myapp.config")
    for p in candidates:
        p = Path(p)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            merged = {**_DEFAULTS, **data}
            merged["camera"] = {**_DEFAULTS["camera"], **data.get("camera", {})}
            merged["engines"] = {**_DEFAULTS["engines"], **data.get("engines", {})}
            merged["logging"] = {**_DEFAULTS["logging"], **data.get("logging", {})}
            merged["_settings_path"] = str(p.resolve())
            log.info("Config chargée depuis %s", p)
            return merged
    merged = _DEFAULTS.copy()
    merged["_settings_path"] = str(Path("settings.yaml").resolve())
    logging.getLogger("myapp.config").warning("Aucun settings.yaml trouvé, defaults utilisés.")
    return merged

def save_settings(settings: dict, path: str | Path | None = None) -> None:
    out = dict(settings)
    out.pop("_settings_path", None)
    p = Path(path or settings.get("_settings_path") or "settings.yaml")
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, sort_keys=False, allow_unicode=True)
