from __future__ import annotations
import importlib, logging
from typing import Any, List

def _resolve(path: str):
    mod_name, cls_name = path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)

def _engine_kwargs(module_cfg: dict, settings: dict) -> dict:
    engine = module_cfg.get("engine")
    if not engine: return {}
    eng_cfg = settings.get("engines", {}).get(engine, {})
    kwargs = {"engine": engine}
    kwargs.update(eng_cfg)
    return kwargs

def load_modules(settings: dict) -> List[Any]:
    log = logging.getLogger("myapp.plugins")
    modules_cfg = settings.get("processing", {}).get("modules", [])
    instances = []
    for m in modules_cfg:
        if not m.get("enabled", False): continue
        cls = _resolve(m["class"])
        kwargs = _engine_kwargs(m, settings)
        try:
            inst = cls(name=m.get("name"), config=settings, **kwargs)
            instances.append(inst)
            log.info("Module chargé: %s", m.get("name", cls.__name__))
        except Exception:
            log.exception("Échec chargement module %s", m["class"])
    return instances
