from src.engine_control import EngineController
from src.ffmpeg_worker import FFmpegStitcher
from src.utils import logger
from config import cfg, PANORAMA_FACES

def main():
    logger.info(f"=== Source Panorama Renderer (FOV {cfg.RIG_FOV}) ===")
    logger.info(f"Total Angles to Render: {len(PANORAMA_FACES)}")
    
    if not cfg.GAME_EXE.exists():
        logger.error(f"HL2 Executable not found at: {cfg.GAME_EXE}")
        return

    try:
        engine = EngineController()
        stitcher = FFmpegStitcher()
    except Exception as e:
        logger.error(f"Init failed: {e}")
        return

    try:
        # 1. Render Phase
        logger.info("Phase 1: Rendering Panorama Faces...")
        sorted_faces = sorted(list(PANORAMA_FACES.keys()))
        for i, face in enumerate(sorted_faces):
            logger.info(f"Progress: {i+1}/{len(sorted_faces)} ({face})")
            engine.render_face(face)
        
        # 2. Stitch Phase
        logger.info("Phase 2: Stitching Video...")
        stitcher.stitch()
        
    except KeyboardInterrupt:
        logger.warning("Interrupted.")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
