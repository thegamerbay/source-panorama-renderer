import subprocess
import time
import shutil
from pathlib import Path
from config import cfg, PANORAMA_FACES
from src.utils import logger
from src.window_input import press_key, click_mouse

class EngineController:
    """Controls the game engine (Portal 2) to render frames."""
    
    def __init__(self):
        # Config path: .../Portal 2/portal2/cfg
        self.cfg_path = cfg.GAME_ROOT / cfg.MOD_DIR / "cfg"
        self.autoexec = self.cfg_path / "autoexec.cfg"
        self.autoexec_bak = self.cfg_path / "autoexec.cfg.bak"
        
        if not self.cfg_path.exists():
            logger.warning(f"Config directory not found at {self.cfg_path}.")
            self.cfg_path.mkdir(parents=True, exist_ok=True)

    def _generate_render_cfg(self, face_name: str, angles: tuple) -> str:
        """Creates the .cfg file with binds and settings."""
        cfg_filename = f"render_{face_name}.cfg"
        pitch, yaw, roll = angles
        REAL_FOV = cfg.RIG_FOV

        content = [
            f"echo \">>> LOADING RENDER CONFIG FOR {face_name} <<<\"", 
            "sv_cheats 1",
            "cl_drawhud 0",
            "r_drawviewmodel 0",
            "crosshair 0",
            "demo_fov_override 0",
            "mat_vignette_enable 0",
            "c_thirdpersonshoulder 0",

            # Clear keys
            "unbind F8", "unbind F9", "unbind F10", "unbind F11", "unbind F12",

            # Binds
            f"bind \"F8\" \"playdemo {cfg.DEMO_FILE}\"",
            f"bind \"F9\" \"sv_cheats 1; mat_vsync 0; fps_max 0; fov {REAL_FOV}; cl_fov {REAL_FOV}; setmodel models/player.mdl; thirdperson; thirdperson_mayamode 1; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180\"",
            f"bind \"F10\" \"demo_gototick 1; demo_pause; sv_cheats 1; fov {REAL_FOV}; cl_fov {REAL_FOV}; setmodel models/player.mdl; thirdperson; thirdperson_mayamode 1; c_thirdpersonshoulder 0; c_mindistance -100; c_minyaw -360; c_maxyaw 360; c_minpitch -180; c_maxpitch 180; cam_idealdist 0; cam_idealdistright 0; cam_idealdistup 0; cam_collision 0; cam_ideallag 0; cam_snapto 1; cam_idealpitch {-pitch}; cam_idealyaw {yaw}; thirdperson; demo_fov_override 0\"",
            f"bind \"F11\" \"fov {REAL_FOV}; cl_fov {REAL_FOV}; thirdperson_mayamode 1; host_framerate {cfg.FRAMERATE}; startmovie {face_name} tga wav; demo_resume\"",
            "bind \"F12\" \"endmovie; quit\""
        ]
        
        file_path = self.cfg_path / cfg_filename
        try:
            with open(file_path, "w", encoding='utf-8') as f:
                f.write("\n".join(content))
        except IOError as e:
            logger.error(f"Failed to write config file {file_path}: {e}")
            raise
        
        return cfg_filename

    def _setup_autoexec(self, render_cfg_name: str):
        """
        Sets up autoexec.cfg to execute our render config automatically on launch.
        """
        # 1. Backup existing autoexec if exists and backup doesn't
        if self.autoexec.exists():
            if not self.autoexec_bak.exists():
                shutil.copy2(self.autoexec, self.autoexec_bak)
        
        # 2. Overwrite autoexec.cfg with our command
        # We add echo to see in console that the file loaded
        content = f"echo \">>> AUTOEXEC LOADED <<<\"; exec {render_cfg_name}\n"
        
        try:
            with open(self.autoexec, "w", encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to setup autoexec: {e}")
            raise

    def _restore_autoexec(self):
        """Restores the original autoexec.cfg."""
        try:
            if self.autoexec.exists():
                self.autoexec.unlink() # Remove our temporary file
            
            if self.autoexec_bak.exists():
                shutil.move(self.autoexec_bak, self.autoexec) # Restore old one
                logger.info("Restored original autoexec.cfg")
        except Exception as e:
            logger.error(f"Failed to restore autoexec: {e}")

    def _cleanup_game_artifacts(self, face_name: str):
        search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "portal2"]
        for mod_path in search_paths:
            if not mod_path.exists(): continue
            for f in mod_path.glob(f"{face_name}*.tga"):
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
        
        # 1. Generate render config
        render_cfg = self._generate_render_cfg(face_name, angles)
        
        # 2. Setup Autoexec to run it
        self._setup_autoexec(render_cfg)
        
        self._cleanup_game_artifacts(face_name)
        
        logger.info(f"--- Starting Render: {face_name} {angles} ---")
        
        # Launch arguments
        cmd = [
            str(cfg.GAME_EXE),
            "-game", cfg.MOD_DIR,
            "-novid",
            "-nojoy",         # Disable joystick
            "-window", "-w", str(cfg.CUBE_FACE_SIZE), "-h", str(cfg.CUBE_FACE_SIZE),
            # We do NOT use +exec here, as autoexec.cfg will load itself
        ]

        process = None
        try:
            logger.info(f"Launching: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, cwd=cfg.GAME_ROOT)
            
            # Wait for load. 
            # Portal 2 loads slowly, better give it a buffer.
            time.sleep(30) 
            
            # Focus window (just in case, but we don't type text anymore)
            logger.info("Clicking to focus window...")
            click_mouse()
            time.sleep(1)

            logger.info("Injecting F8 (Play Demo)...")
            press_key(0x77) 
            time.sleep(15)
            
            logger.info("Injecting F9 (Unlock & Model)...")
            press_key(0x78)
            time.sleep(1)
            
            logger.info("Injecting F10 (Set View)...")
            press_key(0x79)
            time.sleep(2)
            
            logger.info("Injecting F11 (Start Record)...")
            press_key(0x7A)
            
            # --- MONITORING LOOP ---
            monitor_paths = {cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "portal2"}
            monitor_paths = [p for p in monitor_paths if p.exists()]
            tga_pattern = f"{face_name}*.tga"
            
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
                    all_files.sort(key=lambda x: x.stat().st_mtime)
                    
                    if len(all_files) >= 2:
                        check_file = all_files[-2]
                        from src.utils import get_file_md5
                        current_hash = get_file_md5(check_file)
                        
                        if current_hash and current_hash == last_hash:
                            stability_cycles += 1
                        else:
                            stability_cycles = 0
                        last_hash = current_hash
                    
                    if stability_cycles >= 20: 
                        logger.info("Menu detected. Finishing...")
                        press_key(0x7B) # F12
                        try: process.wait(timeout=10)
                        except: process.terminate()
                        break
                except: pass
                time.sleep(2.0)
            
            # Conversion logic (no changes)
            logger.info(f"Processing files for {face_name}...")
            search_paths = [cfg.GAME_ROOT / cfg.MOD_DIR, cfg.GAME_ROOT / "portal2"]
            for mod_path in search_paths:
                if not mod_path.exists(): continue
                
                tga_files = list(mod_path.glob(f"{face_name}*.tga"))
                if not tga_files:
                    continue

                input_pattern = mod_path / f"{face_name}%04d.tga"
                output_pattern = cfg.TEMP_DIR / f"{face_name}%04d.jpg"
                
                logger.info(f"Batch converting {len(tga_files)} frames for {face_name}...")
                
                cmd_base_args = [cfg.FFMPEG_BIN, "-y", "-i", str(input_pattern)]

                try:
                    cmd_nvenc = cmd_base_args + [
                        "-c:v", "mjpeg_nvenc", 
                        "-q:v", "2", 
                        str(output_pattern)
                    ]
                    subprocess.run(cmd_nvenc, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    cmd_cpu = cmd_base_args + [
                        "-c:v", "mjpeg", 
                        "-q:v", "2", 
                        str(output_pattern)
                    ]
                    subprocess.run(cmd_cpu, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                for f in tga_files:
                    try: f.unlink()
                    except: pass
                
                wav_file = mod_path / f"{face_name}.wav"
                if wav_file.exists():
                    target_wav = cfg.TEMP_DIR / f"{face_name}.wav"
                    shutil.move(str(wav_file), target_wav)

        except Exception as e:
            logger.error(f"Render failed for {face_name}: {e}")
            if process and process.poll() is None: process.terminate()
            raise
        finally:
            # Always restore autoexec
            self._restore_autoexec()
