import logging
import os

def setup_logging(cfg: dict | None):
    """Configure le logging global avec console + fichiers séparés."""
    if not cfg:
        logging.basicConfig(level=logging.INFO)
        return

    fmt = cfg.get("format", "[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    level = getattr(logging, cfg.get("level", "INFO").upper(), logging.INFO)
    handlers_cfg = cfg.get("handlers", {})

    logger = logging.getLogger()
    logger.setLevel(level)

    for h in logger.handlers[:]:
        logger.removeHandler(h)

    formatter = logging.Formatter(fmt)

    # --- Console ---
    if handlers_cfg.get("console", True):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # --- Fichier général ---
    file_path = handlers_cfg.get("file")
    if file_path:
        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        err_path = os.path.join(log_dir, "erreurs.log")
        eh = logging.FileHandler(err_path, encoding="utf-8")
        eh.setLevel(logging.ERROR)
        eh.setFormatter(formatter)
        logger.addHandler(eh)


