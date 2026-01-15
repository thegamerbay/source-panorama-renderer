import subprocess
import shutil
from pathlib import Path
from config import cfg
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
        logger.info("--- Starting Panorama Stitching ---")
        
        inputs = []
        
        # 1. Gather Video Inputs
        # The filter 'v360' with input='c3x2' expects a specific grid:
        #   Right Left Up
        #   Down Front Back
        # We need to assemble this grid using discrete inputs.
        
        # Order mapping for our inputs to match v360/c3x2 logical layout:
        # We will stack them manually, so we just need to load them all.
        # Let's define the order we will process them in Python to build the complex filter
        order = ["right", "left", "up", "down", "front", "back"]
        
        missing_files = False
        
        for face in order:
            # Pattern matching: Name%04d.tga (e.g. front0001.tga)
            input_pattern = cfg.TEMP_DIR / f"{face}%04d.tga"
            
            # Simple check if any file exists for this face
            glob_pattern = f"{face}*.tga"
            if not list(cfg.TEMP_DIR.glob(glob_pattern)):
                logger.error(f"Missing frames for face: {face}")
                missing_files = True
                continue
                
            inputs.extend(["-framerate", str(cfg.FRAMERATE), "-i", str(input_pattern)])
            
        if missing_files:
            raise FileNotFoundError("One or more cubemap faces are missing. Cannot stitch.")

        # 2. Gather Audio Input
        # Source Engine records a WAV file for each 'startmovie' session.
        # Format: face.wav
        # All 6 executions produce the same audio, so we just pick 'front'
        audio_path = cfg.TEMP_DIR / "front.wav"
        has_audio = False
        
        if audio_path.exists():
            logger.info(f"Audio source found: {audio_path.name}")
            # Add audio as the next input (Index 6, since 0-5 are video)
            inputs.extend(["-i", str(audio_path)])
            has_audio = True
        else:
            logger.warning("No audio file found (front_.wav). Video will be silent.")

        # 3. Build Filter Complex
        # We have 6 streams: 0, 1, 2, 3, 4, 5 corresponding to Right, Left, Up, Down, Front, Back
        # We want to arrange them into:
        # [0][1][2] -> top row
        # [3][4][5] -> bot row
        # Then stack rows vertically -> grid
        # Then v360 -> equirectangular
        
        filter_complex = (
            "[0:v][1:v][2:v]hstack=inputs=3[top];"
            "[3:v][4:v][5:v]hstack=inputs=3[bot];"
            "[top][bot]vstack=inputs=2[grid];"
            "[grid]v360=input=c3x2:output=equirect:interp=lanczos[outv]"
        )

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
            # Map audio stream from input 6 (the 7th input)
            cmd.extend(["-map", "6:a", "-c:a", "aac", "-b:a", "320k"])
        
        # Video Encoding Settings
        # Trying NVENC for RTX 4080 optimization
        try:
            cmd.extend([
                "-c:v", "hevc_nvenc",      # Nvidia HEVC Encoder
                "-preset", "p7",           # Best Quality
                "-cq", "18",               # Constant Quality factor
                "-pix_fmt", "yuv420p",     # Standard pixel format for compatibility
                str(output_file)
            ])
            logger.info(f"Executing FFmpeg with NVENC...")
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError:
            logger.warning("NVENC encoding failed or returned error. Falling back to libx264 (CPU).")
            # Clear previous failed command options from the failing point? 
            # It's safer to rebuild the command for CPU fallback
            cmd_cpu = [
                self.ffmpeg_bin,
                "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[outv]",
            ]
            if has_audio:
                cmd_cpu.extend(["-map", "6:a", "-c:a", "aac", "-b:a", "320k"])
            
            cmd_cpu.extend([
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                str(output_file)
            ])
            
            subprocess.run(cmd_cpu, check=True)

        logger.info(f"Stitching Complete! Output saved to: {output_file}")
