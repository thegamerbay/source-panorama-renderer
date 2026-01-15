import subprocess
from pathlib import Path
from config import cfg, CUBE_FACES
from src.utils import logger

class EngineController:
    """Controls the game engine (HL2) to render frames."""
    
    def __init__(self):
        # The cfg folder is expected to be inside the mod directory
        self.cfg_path = cfg.GAME_ROOT / cfg.MOD_DIR / "cfg"
        
        if not self.cfg_path.exists():
            logger.warning(f"Config directory not found at {self.cfg_path}. Attempting to create it, but this might be wrong.")
            # We try to create it, but usually it should exist if the path is correct
            self.cfg_path.mkdir(parents=True, exist_ok=True)

    def _generate_render_cfg(self, face_name: str, angles: tuple) -> str:
        """
        Creates a .cfg file with commands to render one face of the cubemap.
        Returns the filename of the created config.
        """
        cfg_filename = f"render_{face_name}.cfg"
        
        # Source Engine 'setang' expects: pitch yaw roll
        pitch, yaw, roll = angles
        
        # Output prefix for frames: e.g. C:/.../temp/front_
        # We use strict forward slashes for Source Engine compatibility
        output_prefix = cfg.TEMP_DIR.absolute() / f"{face_name}_"
        output_prefix_str = str(output_prefix).replace("\\", "/")

        content = [
            "sv_cheats 1",           # Enable cheats for camera control
            "cl_drawhud 0",          # Hide HUD
            "r_drawviewmodel 0",     # Hide weapon models
            "mat_postprocess_enable 0", # Disable post-processing (optional, for cleaner stitch)
            "crosshair 0",           # Hide crosshair
            f"host_framerate {cfg.FRAMERATE}", # Lock framerate for recording
            
            # --- Camera Control ---
            f"fov 90",               # 90 degrees FOV is required for correct cubemap face
            f"setang {pitch} {yaw} {roll}", # Force camera angle
            
            # --- Recording ---
            # 'startmovie' begins recording TGA sequences and a WAV file
            # Format: startmovie <name> tga wav
            f"startmovie \"{output_prefix_str}\" tga wav", 
            
            # Play the demo
            # Note: playdemo might sometimes override viewpoint. 
            # If setang fails, 'drive' or specific demo tools might be needed.
            f"playdemo {cfg.DEMO_FILE}",
            
            # After demo finishes (or if we manually stop it), these run:
            "endmovie",
            "quit"
        ]
        
        # Write the config file
        file_path = self.cfg_path / cfg_filename
        try:
            with open(file_path, "w") as f:
                f.write("\n".join(content))
        except IOError as e:
            logger.error(f"Failed to write config file {file_path}: {e}")
            raise
        
        return cfg_filename

    def render_face(self, face_name: str):
        """
        Launches the game to render the specified face.
        """
        if face_name not in CUBE_FACES:
            raise ValueError(f"Invalid face name: {face_name}")

        angles = CUBE_FACES[face_name]
        cfg_file = self._generate_render_cfg(face_name, angles)
        
        logger.info(f"--- Starting Render: {face_name} {angles} ---")
        
        # Launch Arguments
        # -game: specifies the mod (hl2, episode1, etc)
        # -console: enables console
        # -novid: skips intro video
        # -window -w -h: runs in windowed mode at specific resolution
        # +exec: runs our generated config immediately
        cmd = [
            str(cfg.GAME_EXE),
            "-game", cfg.MOD_DIR,
            "-console",
            "-novid",
            "-window", "-w", str(cfg.CUBE_FACE_SIZE), "-h", str(cfg.CUBE_FACE_SIZE),
            "+exec", cfg_file
        ]

        try:
            logger.info(f"Launching: {' '.join(cmd)}")
            # We wait for the process to finish. 
            # The game should auto-quit because of '+quit' in the cfg.
            subprocess.run(cmd, check=True)
            logger.info(f"Render complete for: {face_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Game process failed for {face_name}: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Game executable not found: {cfg.GAME_EXE}")
            raise
