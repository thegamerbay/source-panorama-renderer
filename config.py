import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class RenderConfig:
    # --- PATHS ---
    # ROOT of the game (Folder containing hl2.exe)
    GAME_ROOT: Path = Path(os.getenv("GAME_ROOT", r"C:\Games\Steam\steamapps\common\Half-Life 2"))
    
    # Path to the executable
    GAME_EXE: Path = GAME_ROOT / "hl2.exe"
    
    # Mod directory (usually 'hl2' for Half-Life 2, 'cstrike' for CSS, etc.)
    MOD_DIR: str = os.getenv("MOD_DIR", "hl2_complete")
    
    # --- RENDER SETTINGS ---
    # Name of the demo file WITHOUT .dem extension
    # The file must be inside the game's folder (e.g. GAME_ROOT/MOD_DIR/my_demo.dem)
    DEMO_FILE: str = os.getenv("DEMO_FILE", "my_gameplay")
    
    # Output name for the final video
    OUTPUT_NAME: str = os.getenv("OUTPUT_NAME", "final_panorama_8k")
    
    # Recording framerate
    FRAMERATE: int = int(os.getenv("FRAMERATE", "60"))
    
    # Resolution of ONE face of the cube.
    # 2048x2048 per face -> ~6K-8K equirectangular panorama
    # 3840x3840 per face -> very high quality 8K
    CUBE_FACE_SIZE: int = int(os.getenv("CUBE_FACE_SIZE", "512"))
    
    # --- FFMPEG SETTINGS ---
    # Command to call ffmpeg (must be in PATH or full path here)
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    
    # Folder for temporary TGA frames
    TEMP_DIR: Path = Path("temp_render_files")

    def __post_init__(self):
        self.output_path = Path("output")
        self.output_path.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)

# Camera Angles for Cubemap (Pitch, Yaw, Roll)
# Source Engine 'setang' format:
# Pitch: -90 (Up) ... 90 (Down)
# Yaw: 0 (Front) ... 90 (Left) ... 180 (Back) ... 270/-90 (Right)
CUBE_FACES = {
    "front": (0, 0, 0),
    "right": (0, 270, 0),
    "back":  (0, 180, 0),
    "left":  (0, 90, 0),
    "up":    (-90, 0, 0), 
    "down":  (90, 0, 0)
}

cfg = RenderConfig()
