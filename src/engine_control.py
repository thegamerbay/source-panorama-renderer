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

        # Calculate FOV for real 90 degrees on 1:1 output
        # For Source Engine (Hor+), this is ~106.26
        REAL_FOV = 106.26

        content = [
            "sv_cheats 1",
            "cl_drawhud 0",
            "r_drawviewmodel 0",
            "crosshair 0",
            # Remove demo limit so fov command works
            "demo_fov_override 0",
            
            # F8: Play Demo
            f"bind F8 \"playdemo {cfg.DEMO_FILE}\"",
            
            # F9: Prepare
            # Add 'fov {REAL_FOV}'
            f"bind F9 \"sv_cheats 1; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180\"",
            
            # F10: Setup Face
            # Removed 'demo_fov_override 110', replaced with 'fov {REAL_FOV}'
            # Important: fov applies after pause, but should work as sv_cheats 1 is set
            f"bind F10 \"demo_gototick 1; demo_pause; sv_cheats 1; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180; cam_idealdist 0; cam_idealdistright 0; cam_idealdistup 0; cam_collision 0; cam_ideallag 0; cam_snapto 1; cam_idealpitch {-pitch}; cam_idealyaw {yaw}; thirdperson; demo_fov_override 0\"",

            # F11: Record
            # Ensure fov is not reset on resume
            f"bind F11 \"fov {REAL_FOV}; thirdperson_mayamode 1; host_framerate {cfg.FRAMERATE}; startmovie {face_name} tga wav; demo_resume\""
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
        cmd = [
            str(cfg.GAME_EXE),
            "-game", cfg.MOD_DIR, # Force 'hl2_complete'
            "-novid",
            "-window", "-w", str(cfg.CUBE_FACE_SIZE), "-h", str(cfg.CUBE_FACE_SIZE),
            "+exec", cfg_file
        ]

        try:
            logger.info(f"Launching: {' '.join(cmd)}")
            
            # Launch game non-blocking
            process = subprocess.Popen(cmd, cwd=cfg.GAME_ROOT)
            
            # Wait for Game Menu to load
            logger.info("Waiting 10 seconds for Menu...")
            import time
            time.sleep(10) 
            
            # Step 1: PLAY (F8)
            logger.info("Injecting F8 (Play Demo)...")
            from src.window_input import press_key
            press_key(0x77) # F8
            
            # Wait for demo load
            logger.info("Waiting 15 seconds for demo load...")
            time.sleep(15)
            
            # Step 2: PREPARE (F9)
            logger.info("Injecting F9 (Unlock Constraints)...")
            press_key(0x78) # F9
            time.sleep(1)
            
            # Step 3: SETUP (F10)
            logger.info("Injecting F10 (Set Face)...")
            press_key(0x79) # F10
            time.sleep(2) # Wait for seek/pause
            
            # Step 4: ACTION (F11)
            logger.info("Injecting F11 (Record)...")
            press_key(0x7A) # F11
            
            logger.info("Render started. Waiting for user to close game...")
            process.wait() # Wait for user to close window
            
            # --- Post-Processing: Move files ---
            logger.info(f"Moving rendered files for {face_name} to temp directory...")
            
            # Search paths: The game might save to MOD_DIR or 'hl2' fallback
            search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"]
            files_moved = False

            for mod_path in search_paths:
                if not mod_path.exists():
                    continue
                    
                # Move TGA sequences (e.g. front0001.tga)
                found_files = list(mod_path.glob(f"{face_name}*.tga"))
                if found_files:
                    logger.info(f"Found {len(found_files)} TGA files in {mod_path}")
                    import shutil
                    for tga_file in found_files:
                        target = cfg.TEMP_DIR / tga_file.name
                        # Handle overwrite if needed or just move
                        if target.exists():
                            target.unlink()
                        shutil.move(str(tga_file), target)
                    files_moved = True

                # Move WAV
                wav_file = mod_path / f"{face_name}.wav"
                if wav_file.exists():
                    logger.info(f"Found audio file in {mod_path}")
                    target_wav = cfg.TEMP_DIR / f"{face_name}.wav"
                    if target_wav.exists():
                        target_wav.unlink()
                    shutil.move(str(wav_file), target_wav)
            
            if not files_moved:
                 logger.warning(f"No output files found for {face_name} in {search_paths}")

            logger.info(f"Render complete for: {face_name}")
        except Exception as e:
            logger.error(f"Game process failed for {face_name}: {e}")
            raise
            logger.error(f"Game process failed for {face_name}: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Game executable not found: {cfg.GAME_EXE}")
            raise
