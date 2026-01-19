import subprocess
import shutil
from pathlib import Path
from config import cfg, PANORAMA_FACES, get_v360_angle
from src.utils import logger

class FFmpegStitcher:
    """Handles the stitching of panoramic faces."""
    
    def __init__(self):
        self.ffmpeg_bin = shutil.which(cfg.FFMPEG_BIN)
        if not self.ffmpeg_bin:
            raise RuntimeError("FFmpeg not found.")

    def stitch(self):
        logger.info(f"--- Starting Panorama Stitching (Multi-Angle Mode: {len(PANORAMA_FACES)} inputs) ---")
        
        inputs = []
        input_pads = []
        angles_list = []
        
        # Sort faces to ensure consistent order (optional but good for debugging)
        # We just need to iterate them and match indices.
        faces_order = sorted(list(PANORAMA_FACES.keys()))
        
        missing_files = False
        
        for idx, face_name in enumerate(faces_order):
            # Input pattern for sequence
            input_pattern = cfg.TEMP_DIR / f"{face_name}%04d.jpg"
            
            # Check for existence
            if not list(cfg.TEMP_DIR.glob(f"{face_name}*.jpg")):
                logger.error(f"Missing frames for face: {face_name}")
                missing_files = True
                continue
                
            # Add Input
            inputs.extend(["-framerate", str(cfg.FRAMERATE), "-i", str(input_pattern)])
            input_pads.append(f"[{idx}:v]")
            
            # Get Angles from config
            src_pitch, src_yaw, _ = PANORAMA_FACES[face_name]
            v_pitch, v_yaw = get_v360_angle(src_pitch, src_yaw)
            
            angles_list.append(f"{v_pitch} {v_yaw}")
            
        if missing_files:
            raise FileNotFoundError("Critical files missing. Aborting stitch.")

        # Audio (Use the first available or a specific one like row0_yaw0)
        audio_face = faces_order[0]
        audio_path = cfg.TEMP_DIR / f"{audio_face}.wav"
        has_audio = False
        audio_input_idx = len(faces_order)
        
        if audio_path.exists():
            inputs.extend(["-i", str(audio_path)])
            has_audio = True

        # Build Filter
        cam_angles_str = " ".join(angles_list)
        pads_str = "".join(input_pads)
        
        # Calculate Output Resolution
        out_w = int((360.0 / cfg.RIG_FOV) * cfg.CUBE_FACE_SIZE)
        out_h = int(out_w / 2)
        
        v360_filter = (
            f"v360=input=tiles:output=equirect:interp=lanczos"
            f":w={out_w}:h={out_h}"
            f":cam_angles='{cam_angles_str}'"
            f":rig_fov={cfg.RIG_FOV}"
            f":blend_width={cfg.BLEND_WIDTH}"
            f"[outv]"
        )
        
        filter_complex = f"{pads_str}{v360_filter}"
        output_file = cfg.output_path / f"{cfg.OUTPUT_NAME}.mp4"

        cmd = [
            self.ffmpeg_bin, "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[outv]"
        ]

        if has_audio:
            cmd.extend(["-map", f"{audio_input_idx}:a", "-c:a", "aac", "-b:a", "320k"])
        
        # NVENC encoding
        try:
            cmd_nvenc = cmd + ["-c:v", "hevc_nvenc", "-pix_fmt", "yuv420p", "-preset", "p7", "-cq", "18", str(output_file)]
            logger.info("Encoding with NVENC...")
            subprocess.run(cmd_nvenc, check=True)
        except subprocess.CalledProcessError:
            logger.warning("NVENC failed, using CPU...")
            cmd_cpu = cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(output_file)]
            subprocess.run(cmd_cpu, check=True)

        logger.info(f"Done! Output: {output_file}")
