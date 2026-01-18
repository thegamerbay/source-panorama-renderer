import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class RenderConfig:
    # --- PATHS ---
    GAME_ROOT: Path = Path(os.getenv("GAME_ROOT", r"C:\Games\Steam\steamapps\common\Half-Life 2"))
    GAME_EXE: Path = GAME_ROOT / "hl2.exe"
    MOD_DIR: str = os.getenv("MOD_DIR", "hl2_complete")
    
    # --- RENDER SETTINGS ---
    DEMO_FILE: str = os.getenv("DEMO_FILE", "my_gameplay")
    OUTPUT_NAME: str = os.getenv("OUTPUT_NAME", "final_panorama_8k")
    FRAMERATE: int = int(os.getenv("FRAMERATE", "60"))
    
    # Resolution of ONE face
    CUBE_FACE_SIZE: int = int(os.getenv("CUBE_FACE_SIZE", "2048"))
    
    # --- FFMPEG SETTINGS ---
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")
    TEMP_DIR: Path = Path("temp_render_files")

    # --- V360 EXTENDED SETTINGS ---
    # FOV for the input camera (Now 60.0 for the new request)
    RIG_FOV: float = float(os.getenv("RIG_FOV", "60.0"))
    
    # Blend width needs to be sufficient for the overlap
    BLEND_WIDTH: float = float(os.getenv("BLEND_WIDTH", "0.05"))

    def __post_init__(self):
        self.output_path = Path("output")
        self.output_path.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)

cfg = RenderConfig()

# --- ANGLES GENERATION ---
# We need to cover the sphere with a 60 degree FOV camera.
# Optimal robust layout: 
# - Equator (Pitch 0): 8 shots (45 deg step)
# - Mid-Latitudes (Pitch +/- 45): 6 shots each (60 deg step)
# - Poles (Pitch +/- 90): 1 shot each
# Total: 22 shots

PANORAMA_FACES = {}

# 1. Equator Ring (8 shots)
for i in range(8):
    yaw = i * 45
    name = f"row0_yaw{yaw}"
    PANORAMA_FACES[name] = (0, yaw, 0) # Pitch, Yaw, Roll

# 2. Upper Ring (Pitch 45, 6 shots)
for i in range(6):
    yaw = i * 60
    name = f"rowUp_yaw{yaw}"
    PANORAMA_FACES[name] = (45, yaw, 0)

# 3. Lower Ring (Pitch -45, 6 shots)
for i in range(6):
    yaw = i * 60
    name = f"rowDown_yaw{yaw}"
    PANORAMA_FACES[name] = (-45, yaw, 0)

# 4. Caps
PANORAMA_FACES["cap_up"] = (90, 0, 0)
PANORAMA_FACES["cap_down"] = (-90, 0, 0)

def get_v360_angle(source_pitch, source_yaw):
    """
    Converts Source Engine angles to FFmpeg v360 angles.
    Source Pitch: -90 (Up) ... 90 (Down) -> engine_control inverts this input usually.
    Actually, in our config:
    Positive Pitch = Up (we invert in engine_control)
    
    Let's standardize based on the previous config:
    Source 'up' was (90,0,0) -> v360 (-90, 0).
    So v360_pitch = -source_pitch.
    
    Source Yaw increases Counter-Clockwise (Left).
    v360 Yaw increases Clockwise (Right).
    v360_yaw = (360 - source_yaw) % 360.
    """
    p = -source_pitch
    y = (360 - source_yaw) % 360
    return p, y
