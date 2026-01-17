import subprocess
import shutil
from pathlib import Path
from config import cfg, V360_ANGLES
from src.utils import logger

class FFmpegStitcher:
    """Handles the stitching of cubemap faces into an immersive video."""
    
    def __init__(self):
        # Verify FFmpeg availability
        self.ffmpeg_bin = shutil.which(cfg.FFMPEG_BIN)
        if not self.ffmpeg_bin:
            logger.error(f"FFmpeg binary not found: {cfg.FFMPEG_BIN}")
            raise RuntimeError("FFmpeg is required but not found. Please install it or check config.py")

    def stitch(self):
        logger.info("--- Starting Panorama Stitching (Rig Mode) ---")
        
        inputs = []
        input_pads = []
        angles_list = []
        
        # Define the order of face processing
        # This order determines the input stream indices: 0, 1, 2, ...
        faces_order = ["right", "left", "up", "down", "front", "back"]
        
        missing_files = False
        
        for idx, face in enumerate(faces_order):
            # Pattern matching: Name%04d.tga (e.g. front0001.tga)
            input_pattern = cfg.TEMP_DIR / f"{face}%04d.tga"
            
            # Check for generic existence
            glob_pattern = f"{face}*.tga"
            if not list(cfg.TEMP_DIR.glob(glob_pattern)):
                logger.error(f"Missing frames for face: {face}")
                # We can either skip or error out. Usually critical failure.
                missing_files = True
                continue
                
            # Add Input Arguments
            inputs.extend(["-framerate", str(cfg.FRAMERATE), "-i", str(input_pattern)])
            
            # Prepare Filter Pads: [0:v], [1:v], etc.
            input_pads.append(f"[{idx}:v]")
            
            # Prepare Camera Angle Pair
            pitch, yaw = V360_ANGLES.get(face, (0, 0))
            angles_list.append(f"{pitch} {yaw}")
            
        if missing_files:
            raise FileNotFoundError("One or more cubemap faces are missing. Cannot stitch.")

        # 2. Gather Audio Input
        # Source Engine audio is usually face specific naming but identical content
        audio_path = cfg.TEMP_DIR / "front.wav"
        has_audio = False
        audio_input_idx = len(faces_order) # The next index after all video inputs
        
        if audio_path.exists():
            logger.info(f"Audio source found: {audio_path.name}")
            inputs.extend(["-i", str(audio_path)])
            has_audio = True
        else:
            logger.warning("No audio file found (front.wav). Video will be silent.")

        # 3. Build Filter Complex for v360 Rig Mode
        # Format: cam_angles='p0 y0 p1 y1 ...'
        cam_angles_str = " ".join(angles_list)
        
        # Concatenate all input pads for the filter
        # e.g. [0:v][1:v][2:v][3:v][4:v][5:v]
        pads_str = "".join(input_pads)
        
        # Construct the v360 filter string
        # rig_fov and blend_width come from config
        v360_filter = (
            f"v360=input=tiles:output=equirect:interp=lanczos"
            f":cam_angles='{cam_angles_str}'"
            f":rig_fov={cfg.RIG_FOV}"
            f":blend_width={cfg.BLEND_WIDTH}"
            f"[outv]"
        )
        
        filter_complex = f"{pads_str}{v360_filter}"
        
        output_file = cfg.output_path / f"{cfg.OUTPUT_NAME}.mp4"

        # 4. Final Command
        cmd = [
            self.ffmpeg_bin,
            "-y", # Overwrite output
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]", # Map the video output from filter
        ]

        if has_audio:
            # Map audio stream
            cmd.extend(["-map", f"{audio_input_idx}:a", "-c:a", "aac", "-b:a", "320k"])
        
        # Video Encoding Settings
        # Trying NVENC for RTX optimizations or Fallback
        try:
            cmd_nvenc = cmd + [
                "-c:v", "hevc_nvenc",
                "-preset", "p7",
                "-cq", "18",
                "-pix_fmt", "yuv420p",
                str(output_file)
            ]
            logger.info(f"Executing FFmpeg with NVENC (Rig Mode)...")
            subprocess.run(cmd_nvenc, check=True)
            
        except subprocess.CalledProcessError:
            logger.warning("NVENC encoding failed. Falling back to libx264 (CPU).")
            # CPU Fallback
            cmd_cpu = cmd + [
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(output_file)
            ]
            subprocess.run(cmd_cpu, check=True)

        logger.info(f"Stitching Complete! Output saved to: {output_file}")
