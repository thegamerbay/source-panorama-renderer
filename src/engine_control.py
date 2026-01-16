import subprocess
import time
import shutil
from pathlib import Path
from config import cfg, CUBE_FACES
from src.utils import logger
from src.window_input import press_key

class EngineController:
    """Controls the game engine (HL2) to render frames."""
    
    def __init__(self):
        # The cfg folder is expected to be inside the mod directory
        self.cfg_path = cfg.GAME_ROOT / cfg.MOD_DIR / "cfg"
        
        if not self.cfg_path.exists():
            logger.warning(f"Config directory not found at {self.cfg_path}. Attempting to create it.")
            self.cfg_path.mkdir(parents=True, exist_ok=True)

    def _generate_render_cfg(self, face_name: str, angles: tuple) -> str:
        """
        Creates a .cfg file with commands to render one face of the cubemap.
        Returns the filename of the created config.
        """
        cfg_filename = f"render_{face_name}.cfg"
        
        pitch, yaw, roll = angles
        
        # Calculate FOV for real 90 degrees on 1:1 output
        REAL_FOV = 106.26

        content = [
            "sv_cheats 1",
            "cl_drawhud 0",
            "r_drawviewmodel 0",
            "crosshair 0",
            "demo_fov_override 0",
            
            # F8: Play Demo
            f"bind F8 \"playdemo {cfg.DEMO_FILE}\"",
            
            # F9: Prepare
            f"bind F9 \"sv_cheats 1; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180\"",
            
            # F10: Setup Face
            f"bind F10 \"demo_gototick 1; demo_pause; sv_cheats 1; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180; cam_idealdist 0; cam_idealdistright 0; cam_idealdistup 0; cam_collision 0; cam_ideallag 0; cam_snapto 1; cam_idealpitch {-pitch}; cam_idealyaw {yaw}; thirdperson; demo_fov_override 0\"",

            # F11: Record
            f"bind F11 \"fov {REAL_FOV}; thirdperson_mayamode 1; host_framerate {cfg.FRAMERATE}; startmovie {face_name} tga wav; demo_resume\"",
            
            # NEW F12: Stop Record and Quit safely
            # 'endmovie' is required to finalize the WAV header properly
            "bind F12 \"endmovie; quit\""
        ]
        
        file_path = self.cfg_path / cfg_filename
        try:
            with open(file_path, "w") as f:
                f.write("\n".join(content))
        except IOError as e:
            logger.error(f"Failed to write config file {file_path}: {e}")
            raise
        
        return cfg_filename

    def _cleanup_game_artifacts(self, face_name: str):
        """Removes existing TGA/WAV files in the game directory to prevent monitoring errors."""
        search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"]
        for mod_path in search_paths:
            if not mod_path.exists(): continue
            
            # Remove existing TGAs
            for f in mod_path.glob(f"{face_name}*.tga"):
                try: f.unlink()
                except: pass
            
            # Remove existing WAV
            wav = mod_path / f"{face_name}.wav"
            if wav.exists():
                try: wav.unlink()
                except: pass

    def render_face(self, face_name: str):
        """
        Launches the game to render the specified face.
        """
        if face_name not in CUBE_FACES:
            raise ValueError(f"Invalid face name: {face_name}")

        angles = CUBE_FACES[face_name]
        cfg_file = self._generate_render_cfg(face_name, angles)
        
        # Cleanup old files first so our count starts at 0
        self._cleanup_game_artifacts(face_name)
        
        logger.info(f"--- Starting Render: {face_name} {angles} ---")
        
        cmd = [
            str(cfg.GAME_EXE),
            "-game", cfg.MOD_DIR,
            "-novid",
            "-window", "-w", str(cfg.CUBE_FACE_SIZE), "-h", str(cfg.CUBE_FACE_SIZE),
            "+exec", cfg_file
        ]

        try:
            logger.info(f"Launching: {' '.join(cmd)}")
            
            process = subprocess.Popen(cmd, cwd=cfg.GAME_ROOT)
            
            # Automation Sequence
            logger.info("Waiting 10 seconds for Menu...")
            time.sleep(10) 
            
            logger.info("Injecting F8 (Play Demo)...")
            press_key(0x77) # F8
            time.sleep(15)
            
            logger.info("Injecting F9 (Unlock Constraints)...")
            press_key(0x78) # F9
            time.sleep(1)
            
            logger.info("Injecting F10 (Set Face)...")
            press_key(0x79) # F10
            time.sleep(2)
            
            logger.info("Injecting F11 (Record)...")
            press_key(0x7A) # F11
            
            logger.info("Recording started. Monitoring frame output to detect completion...")
            
            # --- MONITORING LOOP ---
            # Monitor both MOD_DIR and 'hl2' fallback to catch files wherever engine saves them
            monitor_paths = {cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"}
            # Filter valid existant paths
            monitor_paths = [p for p in monitor_paths if p.exists()]
            
            tga_pattern = f"{face_name}*.tga"
            
            last_hash = ""
            stability_cycles = 0
            check_interval = 2.0  # Check every 2 seconds
            
            # Give the game a moment to actually start writing files
            time.sleep(5)
            
            while True:
                # 1. Check if game crashed or user closed it
                if process.poll() is not None:
                    logger.info("Game process exited externally.")
                    break
                
                # 2. Monitor Output Images
                # We need to check if the generated images are static (menu screen).
                # We look at the penultimate file to avoid reading a file currently being written.
                try:
                    all_files = []
                    for p in monitor_paths:
                        all_files.extend(p.glob(tga_pattern))
                    
                    # Sort by modification time (or name if numbered linearly)
                    # Names are like 'front0001.tga', so sorting by name works.
                    all_files.sort(key=lambda x: x.name)
                    
                    current_count = len(all_files)
                    
                    if current_count >= 2:
                        # Check the second to last file (stable)
                        # We don't check the last one as it might be incomplete
                        check_file = all_files[-2]
                        
                        from src.utils import get_file_md5
                        current_hash = get_file_md5(check_file)
                        
                        logger.info(f"Monitor: Captured {current_count} frames. Top: {check_file.name} [{current_hash}]")
                        
                        if current_hash and current_hash == last_hash:
                            stability_cycles += 1
                            logger.info(f"Hash Stability: {stability_cycles}/5")
                        else:
                            stability_cycles = 0
                            
                        last_hash = current_hash
                    else:
                        logger.info(f"Monitor: Captured {current_count} frames (waiting for more data)...")

                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    stability_cycles = 0

                # If hash is stable for 5 checks (approx 10 seconds), assume finished (static menu)
                if stability_cycles >= 5:
                    logger.info("Render output is static (Menu detected). assuming demo finished.")
                    
                    # 3. Graceful Exit (F12)
                    logger.info("Injecting F12 (Endmovie + Quit)...")
                    press_key(0x7B) # F12 key
                    
                    # Wait for game to close itself
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning("Game did not quit gracefully. Forcing termination...")
                        process.terminate()
                    break
                
                time.sleep(check_interval)
            
            # --- Post-Processing: Move files ---
            logger.info(f"Moving rendered files for {face_name} to temp directory...")
            
            search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"]
            files_moved = False

            for mod_path in search_paths:
                if not mod_path.exists(): continue
                    
                found_files = list(mod_path.glob(f"{face_name}*.tga"))
                if found_files:
                    logger.info(f"Found {len(found_files)} TGA files in {mod_path}")
                    for tga_file in found_files:
                        target = cfg.TEMP_DIR / tga_file.name
                        if target.exists(): target.unlink()
                        shutil.move(str(tga_file), target)
                    files_moved = True

                wav_file = mod_path / f"{face_name}.wav"
                if wav_file.exists():
                    target_wav = cfg.TEMP_DIR / f"{face_name}.wav"
                    if target_wav.exists(): target_wav.unlink()
                    shutil.move(str(wav_file), target_wav)
            
            if not files_moved:
                 logger.warning(f"No output files found for {face_name}")

            logger.info(f"Render complete for: {face_name}")

        except Exception as e:
            logger.error(f"Game process failed for {face_name}: {e}")
            if process.poll() is None:
                process.terminate()
            raise
        except FileNotFoundError:
            logger.error(f"Game executable not found: {cfg.GAME_EXE}")
            raise
