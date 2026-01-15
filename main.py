from src.engine_control import EngineController
from src.ffmpeg_worker import FFmpegStitcher
from src.utils import logger, cleanup_temp
from config import cfg, CUBE_FACES

def main():
    logger.info(f"=== Source Panorama Renderer Started ===")
    logger.info(f"Game Path: {cfg.GAME_EXE}")
    logger.info(f"Demo File: {cfg.DEMO_FILE}")
    logger.info(f"Resolution: {cfg.CUBE_FACE_SIZE}x{cfg.CUBE_FACE_SIZE} per face")
    
    # Validation
    if not cfg.GAME_EXE.exists():
        logger.error(f"HL2 Executable not found at: {cfg.GAME_EXE}")
        logger.error("Please edit config.py with the correct path.")
        return

    # Initialize workers
    try:
        engine = EngineController()
        stitcher = FFmpegStitcher()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return

    try:
        # 1. Render Phase
        logger.info("Phase 1: Rendering Cubemap Faces...")
        for face in CUBE_FACES.keys():
            engine.render_face(face)
        
        # 2. Stitch Phase
        logger.info("Phase 2: Stitching Video...")
        stitcher.stitch()
        
        logger.info("=== Application Finished Successfully ===")
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        # Optional: Cleanup temp files
        # We leave them by default in case debugging is needed, 
        # or user wants to keep the raw frames.
        # cleanup_temp(cfg.TEMP_DIR)
        pass

if __name__ == "__main__":
    main()
