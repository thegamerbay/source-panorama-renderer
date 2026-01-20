import logging
import sys
from pathlib import Path
import shutil

def setup_logger():
    """Configures and returns a standard logger."""
    logger = logging.getLogger("HL2Render")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()

def cleanup_temp(path: Path):
    """Removes a directory and its contents if it exists."""
    if path.exists():
        logger.info(f"Cleaning up temporary files: {path}")
        try:
            shutil.rmtree(path)
        except Exception as e:
            logger.error(f"Failed to cleanup {path}: {e}")

def get_file_md5(file_path: Path) -> str:
    """Calculates the MD5 hash of a file."""
    import hashlib
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to calculate hash for {file_path}: {e}")
        return ""

def install_player_model(game_root: Path, mod_dir: str):
    """Copies the invisible/battery player model to the mod folder to prevent rendering the player."""
    source = Path("assets/player.mdl")
    dest_dir = game_root / mod_dir / "models"
    dest_file = dest_dir / "player.mdl"

    if not source.exists():
        logger.warning(f"Custom player model not found at {source}. Skipping installation.")
        return

    try:
        if not dest_dir.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dest_dir}")

        if not dest_file.exists():
            shutil.copy2(source, dest_file)
            logger.info(f"Installed custom player model to: {dest_file}")
        else:
            logger.info(f"Player model already exists at: {dest_file} (Skipping copy)")
            
    except Exception as e:
        logger.error(f"Failed to install player model: {e}")
