import subprocess
import time
import shutil
from pathlib import Path
from config import cfg, PANORAMA_FACES
from src.utils import logger
from src.window_input import press_key

class EngineController:
    """Controls the game engine (HL2) to render frames."""
    
    def __init__(self):
        self.cfg_path = cfg.GAME_ROOT / cfg.MOD_DIR / "cfg"
        
        if not self.cfg_path.exists():
            logger.warning(f"Config directory not found at {self.cfg_path}. Attempting to create it.")
            self.cfg_path.mkdir(parents=True, exist_ok=True)

    def _generate_render_cfg(self, face_name: str, angles: tuple) -> str:
        """
        Creates a .cfg file with commands to render one face.
        """
        cfg_filename = f"render_{face_name}.cfg"
        
        # Unpack angles (Pitch, Yaw, Roll)
        # Note: In our config, Positive Pitch = Look Up, Negative = Look Down.
        # Source Engine 'cam_idealpitch': Positive = Look Down, Negative = Look Up.
        # But we invert it below {-pitch} to match our intuitive config.
        pitch, yaw, roll = angles
        
        # Use the configured RIG_FOV (60.0)
        # Source fov command usually sets horizontal FOV.
        REAL_FOV = cfg.RIG_FOV

        content = [
            "sv_cheats 1",
            "cl_drawhud 0",
            "r_drawviewmodel 0",
            "crosshair 0",
            "demo_fov_override 0",

            # Temporal Artifacts Fixes
            "cl_clock_correction 0",
            "mat_no_bonylighting 1",
            "r_3dsky 0",

            # Vignette Fix
            "mat_vignette_enable 0",
            
            # F8: Play Demo
            f"bind F8 \"playdemo {cfg.DEMO_FILE}\"",
            
            # F9: Prepare (Reset constraints)
            f"bind F9 \"sv_cheats 1; mat_vsync 0; fps_max 0; jpeg_quality 100; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180\"",
            
            # F10: Setup Face
            # We use {-pitch} because Source Engine positive pitch is DOWN, but our config uses positive for UP.
            f"bind F10 \"demo_gototick 1; demo_pause; sv_cheats 1; fov {REAL_FOV}; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180; cam_idealdist 0; cam_idealdistright 0; cam_idealdistup 0; cam_collision 0; cam_ideallag 0; cam_snapto 1; cam_idealpitch {-pitch}; cam_idealyaw {yaw}; thirdperson; demo_fov_override 0\"",

            # F11: Record
            f"bind F11 \"fov {REAL_FOV}; thirdperson_mayamode 1; host_framerate {cfg.FRAMERATE}; startmovie {face_name} jpeg wav; demo_resume\"",
            
            # F12: Stop Record and Quit
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
        search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"]
        for mod_path in search_paths:
            if not mod_path.exists(): continue
            for f in mod_path.glob(f"{face_name}*.jpg"):
                try: f.unlink()
                except: pass
            wav = mod_path / f"{face_name}.wav"
            if wav.exists():
                try: wav.unlink()
                except: pass

    def render_face(self, face_name: str):
        if face_name not in PANORAMA_FACES:
            raise ValueError(f"Invalid face name: {face_name}")

        angles = PANORAMA_FACES[face_name]
        cfg_file = self._generate_render_cfg(face_name, angles)
        
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
            
            # Automation Sequence (Timing can be adjusted if loading is slow)
            time.sleep(10) 
            logger.info("Injecting F8 (Play Demo)...")
            press_key(0x77) 
            time.sleep(15)
            logger.info("Injecting F9 (Unlock)...")
            press_key(0x78)
            time.sleep(1)
            logger.info("Injecting F10 (Set View)...")
            press_key(0x79)
            time.sleep(2)
            logger.info("Injecting F11 (Start Record)...")
            press_key(0x7A)
            
            # --- MONITORING LOOP (Same as before) ---
            monitor_paths = {cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"}
            monitor_paths = [p for p in monitor_paths if p.exists()]
            tga_pattern = f"{face_name}*.jpg"
            
            last_hash = ""
            stability_cycles = 0
            
            time.sleep(5)
            
            while True:
                if process.poll() is not None:
                    break
                
                try:
                    all_files = []
                    for p in monitor_paths:
                        all_files.extend(p.glob(tga_pattern))
                    all_files.sort(key=lambda x: x.name)
                    
                    if len(all_files) >= 2:
                        check_file = all_files[-2]
                        from src.utils import get_file_md5
                        current_hash = get_file_md5(check_file)
                        
                        if current_hash and current_hash == last_hash:
                            stability_cycles += 1
                        else:
                            stability_cycles = 0
                        last_hash = current_hash
                    
                    if stability_cycles >= 5:
                        logger.info("Menu detected. Finishing...")
                        press_key(0x7B) # F12
                        try: process.wait(timeout=10)
                        except: process.terminate()
                        break
                except: pass
                time.sleep(2.0)
            
            # Move files
            logger.info(f"Moving files for {face_name}...")
            search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "hl2"]
            for mod_path in search_paths:
                if not mod_path.exists(): continue
                for img_file in mod_path.glob(f"{face_name}*.jpg"):
                    target = cfg.TEMP_DIR / img_file.name
                    shutil.move(str(img_file), target)
                wav_file = mod_path / f"{face_name}.wav"
                if wav_file.exists():
                    target_wav = cfg.TEMP_DIR / f"{face_name}.wav"
                    shutil.move(str(wav_file), target_wav)

        except Exception as e:
            logger.error(f"Render failed for {face_name}: {e}")
            if process.poll() is None: process.terminate()
            raise
