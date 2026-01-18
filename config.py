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
    CUBE_FACE_SIZE: int = int(os.getenv("CUBE_FACE_SIZE", "2048"))
    
    # --- FFMPEG SETTINGS ---
    # Command to call ffmpeg (must be in PATH or full path here)
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    
    # Folder for temporary TGA frames
    TEMP_DIR: Path = Path("temp_render_files")

    # --- V360 EXTENDED SETTINGS ---
    # Field of View for the input rig cameras (degrees). Assumes square renders.
    RIG_FOV: float = float(os.getenv("RIG_FOV", "90.0"))
    
    # Width of the soft-edge blending region (normalized 0.0 - 0.5)
    BLEND_WIDTH: float = float(os.getenv("BLEND_WIDTH", "0.05"))

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
    # Fixed: Inverted pitch for Source Engine (Up is negative, but we passed negated in engine_control)
    # We want final engine value: -90 for UP, 90 for DOWN.
    # engine_control uses {-pitch}. 
    # So for UP (-90 engine), we need input 90.
    # So for DOWN (90 engine), we need input -90.
    "up":    (90, 0, 0),   
    "down":  (-90, 0, 0)
}

# FFmpeg v360 'cam_angles' format (Pitch Yaw) pairs.
# Mapping Source Engine faces to v360 logical angles.
# Assuming v360 coordinate system:
# Yaw increases clockwise/counter-clockwise? 
# Usually in 360 tools: 0=Front, 90=Right, 180=Back, 270=Left.
# Source Engine: 0=Front, 90=Left, 180=Back, 270=Right.
# So we need to map Source Faces to appropriate v360 angles.
# Let's assume standard conventions for the output panorama (Equirect):
# Center is Front.
# We map each face to where it looks in the world.
V360_ANGLES = {
    "front": (0, 0),
    "right": (0, 90),   # v360 Right is 90
    "back":  (0, 180),
    "left":  (0, 270),  # v360 Left is 270
    "up":    (90, 0),   # v360 Up
    "down":  (-90, 0)   # v360 Down
}

cfg = RenderConfig()
